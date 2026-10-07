from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.hub_auth import HubUser, current_user, hub_auth
from app.routers import sales

Base.metadata.create_all(bind=engine)

# A doc da API fica debaixo de /api (mesmo prefixo que o nginx repassa pro backend).
# É lá que o Portal de APIs do Twygo Hub busca o /api/openapi.json.
app = FastAPI(title="Indicadores API", openapi_url="/api/openapi.json", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Toda rota de vendas passa pelo login do Hub.
# Em AUTH_MODE=none (padrão) a dependência não faz nada.
app.include_router(sales.router, dependencies=[Depends(current_user)])


@app.get("/api/health")
def health():
    # Fica aberta de propósito: é o que o Docker/Dokploy usa pra saber se a API subiu.
    return {"status": "ok", "auth_mode": hub_auth.mode}


@app.get("/api/me")
def me(user: HubUser | None = Depends(current_user)):
    """Quem está logado. Em AUTH_MODE=none devolve user = null."""
    if user is None:
        return {"auth_mode": hub_auth.mode, "user": None}
    return {"auth_mode": hub_auth.mode, "user": {"email": user.email, "name": user.name, "role": user.role}}
