from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://kick:kick@postgres:5432/kickfleet"
    redis_url: str = "redis://redis:6379/0"
    fernet_key: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    api_token: str = ""
    env: str = "development"
    stale_worker_seconds: int = 20
    docker_worker_names: str = "kick-worker-01,kick-worker-02,kick-worker-03"


settings = Settings()
