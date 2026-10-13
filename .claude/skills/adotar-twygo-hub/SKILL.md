---
name: adotar-twygo-hub
description: Use quando um app interno da Twygo (Dokploy, *.apps.twygo.com) precisa entrar no Twygo Hub — login único Microsoft Entra, permissão por app e papel, gateway de APIs e barra do Hub. Cobre AUTH_MODE=hub|local, validação do X-Hub-Token pela JWKS, mapeamento de papéis, OpenAPI no caminho certo, rede do compose, barra do Hub e o passo a passo para ligar e voltar. Triggers: "colocar o app no Hub", "adotar o login do Hub", "AUTH_MODE=hub", "X-Hub-Token", "aparecer no portal de APIs", "app novo no Dokploy com login Microsoft".
---

# Adotar o Twygo Hub num app

O Twygo Hub (`https://hub.apps.twygo.com`, repo `Twygo/hub-apps`) fica **na frente** dos apps internos. O login é só Microsoft Entra (tenant Twygo); o Hub decide quem entra em cada app e com qual papel, e repassa a identidade num JWT assinado. O app **não chama o Hub** durante a requisição: só valida o token com a chave pública (JWKS, com cache). Referências completas no repo do Hub: `docs/CONTRATO.md`, `docs/ARQUITETURA.md`, `examples/fastapi/hub_auth.py`, `examples/node/hubAuth.js`.

## Regra de ouro

- Confie **só** no `X-Hub-Token` validado. Os headers `X-Hub-*` em texto são conveniência e podem ser forjados por quem estiver na mesma rede.
- `AUTH_MODE=local` é o padrão e mantém o app **exatamente** como está. Mergear a adoção não muda nada até alguém ligar `AUTH_MODE=hub` no Dokploy.
- Nunca apague o login legado: ele é o caminho de volta (break-glass).

## O token

Header `X-Hub-Token`, JWT RS256, válido por 5 min:

| Claim | Conteúdo |
|---|---|
| `iss` | `https://hub.apps.twygo.com` |
| `aud` | slug do app no catálogo do Hub (ex.: `renewals`, `awards`, `customer-sheet`) |
| `sub` | e-mail da pessoa |
| `name`, `groups` | nome e grupos do Entra (IDs) |
| `role` | papel da pessoa **neste app** (lista de papéis definida no catálogo, do mais forte ao mais fraco) |
| `app`, `ver` | slug e versão do contrato (`1`) |
| `iat`, `exp` | emissão e expiração |
| header `kid` | chave usada; JWKS em `https://hub.apps.twygo.com/.well-known/jwks.json` |

Validação: `alg` RS256, `iss`, `aud` = slug, `exp` com 30 s de tolerância; cache da JWKS e nova busca quando aparecer `kid` desconhecido (no máximo 1 por 30 s).

## Checklist de adoção

1. **Flag**: `AUTH_MODE` (`local` padrão | `hub`), `HUB_JWKS_URL` (padrão a URL acima), `HUB_ISSUER`, `HUB_AUDIENCE` (= slug).
2. **Validador**: copie o exemplo do Hub para o stack do app (FastAPI: dependência; Express/Next: middleware; Flask: decorator/`before_request`). Em `hub`, toda rota protegida usa a identidade do token.
3. **Usuário**: crie/atualize no primeiro acesso a partir de `sub`/`name`. Não peça senha.
4. **Papéis**: mapeie `role` do Hub para o modelo de permissão do app e documente a tabela no README.
5. **Sem token** (em `hub`): API → 401 JSON; página → tela curta "Acesse pelo Twygo Hub" com link para o Hub.
6. **Logout** (em `hub`): `https://auth.apps.twygo.com/oauth2/sign_out?rd=https://hub.apps.twygo.com`.
7. **OpenAPI** para aparecer no Portal de APIs: publique o documento **no mesmo prefixo que o nginx do app repassa ao backend**. Em FastAPI atrás de nginx com `/api/`: `FastAPI(openapi_url="/api/openapi.json", docs_url=None)`. Se o backend responde na raiz (sem nginx), `/openapi.json` basta. Sem OpenAPI (Flask/Express): registre na PR, não invente.
8. **Rede**: o Hub alcança o app pela `dokploy-network`, pelo **nome de serviço**. Use nomes de serviço únicos e prefixados (`<app>-web`, `<app>-api`) — `web`, `api`, `frontend` colidem com outros apps. O compose **não** pode estar com *Isolated Deployment* ligado no Dokploy. A API pode continuar privada atrás do nginx do web (`/api/`).
9. **Barra do Hub** (opcional, só em `hub`): `<script src="https://hub.apps.twygo.com/bar.js" defer></script>`; se o app tem CSP, libere `hub.apps.twygo.com` em `script-src` e `connect-src`, e `fonts.googleapis.com`/`fonts.gstatic.com`.
10. **Testes**: par RSA gerado no teste + JWKS falsa: token válido, `aud` errado, expirado, assinatura inválida, `local` sem mudança, criação de usuário, mapeamento de papel.
11. **README**: seção "Autenticação pelo Twygo Hub" com envs, como ligar, como voltar e a tabela de papéis.
12. **Este arquivo**: mantenha a skill `.claude/skills/adotar-twygo-hub/SKILL.md` no repo do app (cópia desta).

## Como ligar em produção (ordem)

1. Merge da adoção (com `AUTH_MODE=local`) e deploy — nada muda.
2. No Hub (Admin › Apps): preencher endereço interno (`upstream_url`), endereço interno da API (`api_upstream`) e caminho do OpenAPI; dar permissão a quem já usa o app (grupo do Entra ou pessoas) **antes** de ativar.
3. Ativar o app no Hub → o domínio passa a exigir login Microsoft + permissão.
4. Trocar `AUTH_MODE=hub` no Dokploy e redeployar → o app usa a identidade do Hub e some o login duplo.
5. Opcional (modo estrito): remover o domínio do app no painel do Dokploy; a única rota passa a ser a do Hub.

## Como voltar

- Rápido: desativar o app no Hub (o Traefik volta à rota do Dokploy) **e** `AUTH_MODE=local` no Dokploy → login antigo do app.
- Emergência no Hub inteiro: `HUB_ROUTES_ENABLED=0` no Hub (tira todas as rotas dos apps de uma vez).

## Gateway de APIs

`https://api.apps.twygo.com/<slug>/<rota>` → o Hub remove `/<slug>` e encaminha ao `api_upstream` com o `X-Hub-Token`. "Exposto para quem tem permissão": só alcança o app quem tem papel nele. Backend chamando outro app em nome da pessoa: `POST http://hub-api:8000/token/exchange` (só rede interna) com `{subject_token, audience}`.
