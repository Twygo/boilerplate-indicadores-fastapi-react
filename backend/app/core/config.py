from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://indicadores:indicadores@db:5432/indicadores"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Login pelo Twygo Hub (ver README, seção "Publicar no Dokploy atrás do Twygo Hub") ---
    # "none" = sem login nenhum (padrão, bom pra rodar local e brincar).
    # "hub"  = toda rota de /api exige o X-Hub-Token que o Twygo Hub manda.
    auth_mode: str = "none"
    # De onde baixar as chaves públicas do Hub (JWKS).
    hub_jwks_url: str = "https://hub.apps.twygo.com/.well-known/jwks.json"
    # Quem assina o token (claim "iss").
    hub_issuer: str = "https://hub.apps.twygo.com"
    # Slug do seu app no Hub (claim "aud"). Troque pelo slug cadastrado no Hub.
    hub_audience: str = "indicadores"

    class Config:
        env_file = ".env"


settings = Settings()
