"""Testes do login pelo Twygo Hub (app/core/hub_auth.py).

Ninguém aqui fala com o Hub de verdade: cada teste gera um par de chaves RSA,
assina tokens com a chave privada e serve a chave pública numa JWKS falsa.
Rodar: cd backend && pip install -r requirements-dev.txt && pytest
"""
import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.hub_auth import HubAuth, HubUser, current_user

ISS = "https://hub.apps.twygo.com"
JWKS_URL = "https://hub.test/.well-known/jwks.json"
SLUG = "indicadores"


# --- Ajudantes -----------------------------------------------------------------
def nova_chave():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwk_da(chave_privada, kid):
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(chave_privada.public_key()))
    jwk.update(kid=kid, use="sig", alg="RS256")
    return jwk


class JwksFalsa:
    """Faz o papel do https://hub.apps.twygo.com/.well-known/jwks.json e conta as buscas."""

    def __init__(self, *keys):
        self.keys = list(keys)
        self.buscas = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert str(request.url) == JWKS_URL
        self.buscas += 1
        return httpx.Response(200, json={"keys": self.keys})


def gera_token(chave_privada, kid="k1", **trocas):
    agora = int(time.time())
    claims = {
        "iss": ISS, "aud": SLUG, "sub": "Maria@twygo.com", "name": "Maria Souza",
        "app": SLUG, "role": "editor", "groups": ["g1"], "ver": 1,
        "iat": agora, "exp": agora + 300,
    }
    claims.update(trocas)
    return jwt.encode(claims, chave_privada, algorithm="RS256", headers={"kid": kid})


def monta_app(jwks, mode="hub"):
    """App FastAPI mínimo com uma rota protegida pela HubAuth."""
    auth = HubAuth(
        mode=mode, audience=SLUG, issuer=ISS, jwks_url=JWKS_URL,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(jwks.handler)),
    )
    app = FastAPI()

    @app.get("/api/me")
    async def me(user: HubUser | None = Depends(auth)):
        if user is None:
            return None
        return {"email": user.email, "name": user.name, "role": user.role}

    return TestClient(app)


def chama(client, token=None):
    return client.get("/api/me", headers={"X-Hub-Token": token} if token else {})


@pytest.fixture
def chave():
    return nova_chave()


@pytest.fixture
def jwks(chave):
    return JwksFalsa(jwk_da(chave, "k1"))


# --- AUTH_MODE=hub -------------------------------------------------------------
def test_token_valido_devolve_email_nome_e_papel(chave, jwks):
    r = chama(monta_app(jwks), gera_token(chave))
    assert r.status_code == 200
    assert r.json() == {"email": "maria@twygo.com", "name": "Maria Souza", "role": "editor"}


def test_jwks_fica_em_cache(chave, jwks):
    client = monta_app(jwks)
    for _ in range(3):
        assert chama(client, gera_token(chave)).status_code == 200
    assert jwks.buscas == 1


def test_aud_errado_e_recusado(chave, jwks):
    assert chama(monta_app(jwks), gera_token(chave, aud="outro-app")).status_code == 401


def test_token_expirado_e_recusado(chave, jwks):
    agora = int(time.time())
    token = gera_token(chave, iat=agora - 400, exp=agora - 60)
    assert chama(monta_app(jwks), token).status_code == 401


def test_assinatura_invalida_e_recusada(chave, jwks):
    intruso = nova_chave()  # mesma "cara" de token, mas assinado por outra chave
    assert chama(monta_app(jwks), gera_token(intruso, kid="k1")).status_code == 401


def test_iss_errado_e_recusado(chave, jwks):
    assert chama(monta_app(jwks), gera_token(chave, iss="https://evil.example")).status_code == 401


def test_kid_desconhecido_e_recusado(chave, jwks):
    assert chama(monta_app(jwks), gera_token(chave, kid="nao-existe")).status_code == 401


def test_sem_token_e_recusado(jwks):
    assert chama(monta_app(jwks)).status_code == 401


def test_header_em_texto_nao_vale_sem_token(jwks):
    client = monta_app(jwks)
    r = client.get("/api/me", headers={"X-Hub-User-Email": "chefe@twygo.com", "X-Hub-Role": "admin"})
    assert r.status_code == 401


# --- AUTH_MODE=none (padrão) -----------------------------------------------------
def test_modo_none_libera_sem_token(jwks):
    r = chama(monta_app(jwks, mode="none"))
    assert r.status_code == 200 and r.json() is None
    assert jwks.buscas == 0  # nem chega a buscar a JWKS


def test_modo_padrao_do_boilerplate_e_none():
    app = FastAPI()

    @app.get("/api/coisa")
    async def coisa(user: HubUser | None = Depends(current_user)):
        return {"user": user}

    assert TestClient(app).get("/api/coisa").json() == {"user": None}


def test_auth_mode_invalido_da_erro():
    with pytest.raises(ValueError):
        HubAuth(mode="talvez")


def test_modo_hub_exige_audience():
    with pytest.raises(ValueError):
        HubAuth(mode="hub", audience="")
