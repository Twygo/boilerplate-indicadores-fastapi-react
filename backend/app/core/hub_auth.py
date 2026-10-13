"""Login pelo Twygo Hub.

Quando o app está publicado atrás do Twygo Hub, todo request chega com o
header ``X-Hub-Token``: um JWT assinado pelo Hub (RS256, vale 5 minutos) que diz
quem é a pessoa (``sub`` = e-mail, ``name``) e qual o papel dela no app
(``role``). Este módulo confere esse token.

Como usar numa rota::

    from app.core.hub_auth import HubUser, current_user

    @router.get("/coisa")
    def coisa(user: HubUser | None = Depends(current_user)):
        ...  # user é None quando AUTH_MODE=none

O modo vem da env ``AUTH_MODE``:

- ``none`` (padrão): não confere nada e devolve ``None``. O app fica aberto,
  igualzinho ao boilerplate original.
- ``hub``: exige um ``X-Hub-Token`` válido. Sem token, ou com token inválido,
  responde 401.

Regra de ouro: confie só no token validado. Os headers em texto
(``X-Hub-User-Email``, ``X-Hub-Role``...) podem ser forjados e não valem para
decidir acesso.

Adaptado de ``examples/fastapi/hub_auth.py`` do repo ``Twygo/hub-apps``
(contrato v1, ``docs/CONTRATO.md``).
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, Request

from app.core.config import settings

log = logging.getLogger("hub_auth")

# Versões do contrato que este código entende (claim "ver").
CONTRACT_VERSIONS = {1}
# Modos aceitos. "local" é o nome usado na doc do Hub; aqui vale o mesmo que "none".
MODES = {"none", "local", "hub"}


@dataclass(frozen=True)
class HubUser:
    """Quem está usando o app, segundo o token do Hub."""

    email: str
    name: str
    role: str
    app: str
    groups: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)


class HubAuth:
    """Confere o X-Hub-Token. Guarda as chaves do Hub (JWKS) em cache."""

    def __init__(
        self,
        *,
        mode: str = "none",
        audience: str = "",
        issuer: str = "https://hub.apps.twygo.com",
        jwks_url: str = "https://hub.apps.twygo.com/.well-known/jwks.json",
        cache_ttl: float = 3600,  # guarda a JWKS por 1 hora
        min_refetch_interval: float = 30,  # no máximo 1 busca extra a cada 30 s
        leeway: float = 30,  # tolerância de relógio
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        mode = (mode or "none").strip().lower()
        if mode not in MODES:
            raise ValueError(f"AUTH_MODE inválido: {mode!r} (use none ou hub)")
        if mode == "local":
            mode = "none"
        if mode == "hub" and not audience:
            raise ValueError("AUTH_MODE=hub exige HUB_AUDIENCE (o slug do app no Hub)")
        self.mode = mode
        self.audience = audience
        self.issuer = issuer
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self.min_refetch_interval = min_refetch_interval
        self.leeway = leeway
        self._client = http_client
        self._keys: dict[str, Any] | None = None
        self._fetched_at = 0.0
        self._forced_at = float("-inf")
        self._lock = asyncio.Lock()

    # --- Chaves públicas do Hub (JWKS) ---------------------------------------
    async def _fetch(self) -> None:
        client = self._client or httpx.AsyncClient(timeout=5)
        try:
            resp = await client.get(self.jwks_url)
            resp.raise_for_status()
            keys: dict[str, Any] = {}
            for jwk in resp.json().get("keys", []):
                if jwk.get("kty") != "RSA" or not jwk.get("kid"):
                    continue
                keys[jwk["kid"]] = jwt.PyJWK(jwk, algorithm="RS256").key
            self._keys = keys
            self._fetched_at = time.monotonic()
        finally:
            if self._client is None:
                await client.aclose()

    async def _key_for(self, kid: str) -> Any | None:
        async with self._lock:
            now = time.monotonic()
            if self._keys is None or now - self._fetched_at > self.cache_ttl:
                try:
                    await self._fetch()
                except Exception as exc:  # Hub fora: segue com o cache vencido, se tiver
                    if self._keys is None:
                        log.warning("JWKS indisponível: %s", exc)
                        return None
                    log.warning("JWKS indisponível, usando cache vencido: %s", exc)
            if kid in self._keys:
                return self._keys[kid]
            # kid desconhecido (o Hub pode ter trocado a chave): busca de novo, com limite
            if now - self._forced_at >= self.min_refetch_interval:
                self._forced_at = now
                try:
                    await self._fetch()
                except Exception as exc:
                    log.warning("nova busca da JWKS falhou: %s", exc)
            return self._keys.get(kid)

    # --- Validação do token ----------------------------------------------------
    async def verify(self, token: str) -> HubUser:
        """Valida o token e devolve o usuário. Levanta ``jwt.InvalidTokenError`` se falhar."""
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise jwt.InvalidAlgorithmError("alg precisa ser RS256")
        kid = header.get("kid")
        if not kid:
            raise jwt.InvalidTokenError("token sem kid")
        key = await self._key_for(kid)
        if key is None:
            raise jwt.InvalidKeyError(f"kid desconhecido: {kid}")
        # Confere assinatura, iss, aud e exp (com a tolerância de relógio).
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            leeway=self.leeway,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
        if claims.get("ver") not in CONTRACT_VERSIONS:
            raise jwt.InvalidTokenError(f"versão de contrato não suportada: {claims.get('ver')!r}")
        return HubUser(
            email=str(claims["sub"]).lower(),
            name=claims.get("name") or "",
            role=claims.get("role") or "",
            app=claims.get("app") or "",
            groups=list(claims.get("groups") or []),
            claims=claims,
        )

    async def __call__(self, request: Request) -> HubUser | None:
        if self.mode == "none":
            return None
        token = request.headers.get("x-hub-token")
        if not token:
            raise HTTPException(401, "Acesse pelo Twygo Hub", headers={"WWW-Authenticate": "Bearer"})
        try:
            return await self.verify(token)
        except jwt.PyJWTError as exc:
            log.info("X-Hub-Token rejeitado: %s", exc)
            raise HTTPException(401, "Token do Hub inválido", headers={"WWW-Authenticate": "Bearer"}) from None


# Uma instância só, configurada pelas envs (AUTH_MODE, HUB_AUDIENCE, ...).
hub_auth = HubAuth(
    mode=settings.auth_mode,
    audience=settings.hub_audience,
    issuer=settings.hub_issuer,
    jwks_url=settings.hub_jwks_url,
)


async def current_user(request: Request) -> HubUser | None:
    """Dependência do FastAPI: devolve quem está logado (ou None em AUTH_MODE=none)."""
    return await hub_auth(request)
