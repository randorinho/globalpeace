from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://gpai:gpai@localhost:5432/gpai"
    # Shared secret the Workers gateway sends; origin rejects requests without it.
    # In production the Tunnel + Cloudflare Access service token is the real gate;
    # this is defense in depth.
    gateway_shared_secret: str = "dev-only-change-me"
    environment: str = "development"
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "gpai-dev-password"

    model_config = {"env_prefix": "GPAI_"}


settings = Settings()
