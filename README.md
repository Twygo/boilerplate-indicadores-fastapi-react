# Boilerplate de Indicadores — FastAPI + React + Postgres

Boilerplate pra turma de vibe coding montar dashboard/indicadores em cima de
uma base que já sobe funcionando: API pronta, banco populado com dados fake,
front com gráfico e filtro já ligados na API. A ideia é começar direto na
parte divertida (trocar os dados, criar gráfico novo, mexer no filtro) sem
perder tempo com setup.

## Stack

- **Backend**: FastAPI + SQLAlchemy + Postgres. Sem Alembic de propósito —
  as tabelas são criadas automaticamente no startup (`Base.metadata.create_all`).
  Se a turma quiser aprender migration depois, é só adicionar.
- **Frontend**: React + Vite + TypeScript + [Recharts](https://recharts.org/)
  (gráfico de linha, barra e pizza já prontos em `src/components/Charts.tsx`).
- **Banco**: Postgres 16, com seed de ~1200 vendas fake (Faker) espalhadas nos
  últimos 12 meses, com categoria / região / canal — dá pra filtrar e agrupar
  de várias formas diferentes.

## Subir o projeto

```bash
docker compose up --build
```

Isso sobe banco (5432), API (8000) e front (5173). Depois, popula o banco:

```bash
docker compose exec backend python -m app.seed
```

Abre http://localhost:5173 — o dashboard já deve aparecer com dados.

Doc interativa da API: http://localhost:8000/api/docs (o OpenAPI fica em `/api/openapi.json`)

## Estrutura

```
backend/
  app/
    core/        # config, conexão com banco e login pelo Twygo Hub (hub_auth.py)
    models/      # tabelas (SQLAlchemy) — hoje só "Sale"
    schemas/     # formatos de entrada/saída (Pydantic)
    routers/     # rotas da API
    seed.py      # popula o banco com dados fake
    main.py      # ponto de entrada do FastAPI
  tests/         # testes (pytest)
frontend/
  src/
    components/  # FilterBar, KpiCards, Charts
    lib/api.ts   # chamadas pra API
    lib/hub.ts   # barra do Twygo Hub e tratamento do 401
    App.tsx      # monta a tela
```

## Endpoints principais

- `GET /api/sales` — lista vendas (aceita `date_from`, `date_to`, `category`,
  `region`, `channel`, `limit`, `offset`).
- `GET /api/sales/summary` — indicadores agregados (receita total, unidades,
  ticket médio, série por mês/categoria/região/canal) — é o que os gráficos
  consomem. Aceita os mesmos filtros de cima.
- `GET /api/sales/filters/options` — valores possíveis pra popular os
  dropdowns de filtro.
- `GET /api/me` — quem está logado (em `AUTH_MODE=none` devolve `user: null`).
- `GET /api/health` — sempre aberto, usado pra saber se a API subiu.

## Ideias pra turma expandir

- Trocar o domínio "vendas" por outro dataset (ex: chamados de suporte,
  matrículas, o que fizer sentido) — só criar um `Model` novo e replicar o
  padrão de `sales.py`.
- Adicionar mais um gráfico (ex: `AreaChart` do Recharts) puxando um agrupamento
  novo no `summary`.
- Adicionar paginação/ordenação numa tabela de detalhe usando `GET /api/sales`.
- Trocar Recharts por outra lib (nivo, visx, chart.js) — a API não muda.
- Adicionar autenticação, cache, export CSV, etc.

## Rodando sem Docker (opcional)

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://indicadores:indicadores@localhost:5432/indicadores
uvicorn app.main:app --reload
python -m app.seed
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Publicar no Dokploy atrás do Twygo Hub

O [Twygo Hub](https://hub.apps.twygo.com) fica **na frente** dos apps internos:
ele faz o login Microsoft, decide quem pode entrar em cada app e repassa quem é
a pessoa num token assinado (header `X-Hub-Token`). Este boilerplate já sabe
conferir esse token. **Por padrão isso vem desligado** (`AUTH_MODE=none`): rodando
local, nada muda.

O passo a passo completo (e o porquê de cada item) está na skill
[`.claude/skills/adotar-twygo-hub/SKILL.md`](.claude/skills/adotar-twygo-hub/SKILL.md).
Abaixo, o caminho curto para um app novo feito a partir deste boilerplate.

### 1. Dê nomes únicos aos serviços

Todos os apps do Dokploy dividem a mesma rede. Nomes como `web`, `api` ou
`frontend` batem com os de outros apps. O `docker-compose.dokploy.yml` usa o
prefixo `meuapp`; troque pelo slug do seu app (ex.: `metas-comercial`):

```bash
sed -i 's/meuapp/metas-comercial/g' docker-compose.dokploy.yml
```

### 2. Confira a rede

No `docker-compose.dokploy.yml` já está assim (não precisa mexer):

- `<slug>-web` (nginx com o front, repassa `/api/` pra API) fica na rede
  `interna` **e** na `dokploy-network` (`external: true`). É por ela que o
  Traefik e o Hub chegam no app.
- `<slug>-api` e `<slug>-db` ficam **só** na rede `interna`.
- Nenhum serviço publica porta no host (`ports:`).

No Dokploy, **não** ligue o *Isolated Deployment* desse compose.

### 3. Configure as envs no Dokploy

| Variável | Padrão | Pra que serve |
|---|---|---|
| `POSTGRES_PASSWORD` | — (obrigatória) | Senha do banco de produção. |
| `AUTH_MODE` | `none` | `none` = sem login. `hub` = exige o `X-Hub-Token`. Comece com `none`. |
| `HUB_AUDIENCE` | `meuapp` (`indicadores` fora do compose) | Slug do app no Hub. Tem que ser igual ao cadastrado lá. |
| `HUB_ISSUER` | `https://hub.apps.twygo.com` | Quem assina o token. Não precisa mudar. |
| `HUB_JWKS_URL` | `https://hub.apps.twygo.com/.well-known/jwks.json` | De onde vêm as chaves públicas do Hub. Dentro da `dokploy-network` também dá pra usar `http://hub-api:8000/.well-known/jwks.json`. |
| `VITE_HUB_BAR` | `1` no compose do Dokploy, `0` local | `1` mostra a barra do Hub no topo. Entra no build: mudou, faça novo deploy. |

### 4. Faça o deploy

No Dokploy: crie um **Compose** apontando pro repositório, com o arquivo
`docker-compose.dokploy.yml`, e cadastre o domínio (ex.:
`metas-comercial.apps.twygo.com`) no serviço `<slug>-web`, porta `80`. Faça o
deploy ainda com `AUTH_MODE=none` e confira que o app abre.

Banco novo começa vazio. Pra ter os dados de exemplo, rode uma vez no terminal
do container da API: `python -m app.seed`.

### 5. Cadastre o app no Hub

Peça a um admin do Hub (Admin › Apps) para cadastrar:

| Campo | Valor |
|---|---|
| Slug | o mesmo de `HUB_AUDIENCE` |
| Endereço interno (upstream) | `http://<slug>-web:80` |
| Endereço interno da API | `http://<slug>-web:80` (a API fica atrás do nginx) |
| Caminho do OpenAPI | `/api/openapi.json` |
| Papéis | ex.: `admin`, `editor`, `viewer` |

Com isso o app aparece no Portal de APIs do Hub e fica disponível em
`https://api.apps.twygo.com/<slug>/api/...`.

### 6. Dê permissão a quem vai usar

Ainda no Hub, dê acesso aos grupos do Entra (ou pessoas) **antes** de ativar.
Quem não tiver permissão recebe "sem acesso".

### 7. Ative o app no Hub

A partir daqui o domínio passa a exigir login Microsoft + permissão. O app
ainda está em `AUTH_MODE=none`, então segue funcionando igual.

### 8. Ligue `AUTH_MODE=hub`

Troque `AUTH_MODE=hub` nas envs do Dokploy e faça redeploy. Agora toda rota de
`/api` confere o token. Quem tentar abrir o app sem passar pelo Hub vê
"Acesse pelo Twygo Hub".

Pra usar quem está logado numa rota:

```python
from app.core.hub_auth import HubUser, current_user

@router.get("/minhas-coisas")
def minhas_coisas(user: HubUser | None = Depends(current_user)):
    # user.email, user.name, user.role  (user é None em AUTH_MODE=none)
    ...
```

**Regra de ouro:** confie só no `user` que vem do token validado. Os headers
em texto (`X-Hub-User-Email`, `X-Hub-Role`...) podem ser forjados.

### Como voltar

Deu problema? Troque `AUTH_MODE=none` no Dokploy e faça redeploy, e peça ao
admin pra desativar o app no Hub. O app volta a abrir sem login.
