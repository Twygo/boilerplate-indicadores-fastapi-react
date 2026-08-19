from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://indicadores:indicadores@db:5432/indicadores"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
