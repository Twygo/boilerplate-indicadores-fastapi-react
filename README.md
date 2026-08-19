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

Doc interativa da API: http://localhost:8000/docs

## Estrutura

```
backend/
  app/
    core/        # config + conexão com banco
    models/      # tabelas (SQLAlchemy) — hoje só "Sale"
    schemas/     # formatos de entrada/saída (Pydantic)
    routers/     # rotas da API
    seed.py      # popula o banco com dados fake
    main.py      # ponto de entrada do FastAPI
frontend/
  src/
    components/  # FilterBar, KpiCards, Charts
    lib/api.ts   # chamadas pra API
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
