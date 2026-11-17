from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    worker_id: str = "worker-01"
    worker_name: str = "Worker 01"
    controller_url: str = "http://controller:8000"
    redis_url: str = "redis://redis:6379/0"
    api_token: str = ""
    kick_base_url: str = "https://kick.com"
    screen_width: int = 1920
    screen_height: int = 1080
    novnc_public_url: str = "http://localhost:6081"
    claude_extension_dir: str = ""
    profile_dir: str = "/data/profile"
    headed: bool = True


settings = Settings()
