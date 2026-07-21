from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    backend_url: str = Field(default="http://127.0.0.1:8000", alias="SHIELDNET_BACKEND_URL")
    internal_service_token: str = Field(alias="SHIELDNET_INTERNAL_SERVICE_TOKEN")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="SHIELDNET_REDIS_URL")
    worker_queue: str = Field(default="shieldnet:discord:jobs", alias="SHIELDNET_WORKER_QUEUE")
    log_level: str = Field(default="INFO", alias="SHIELDNET_LOG_LEVEL")
    guild_sync_minutes: int = Field(default=5, alias="SHIELDNET_GUILD_SYNC_MINUTES")
    role_sync_minutes: int = Field(default=15, alias="SHIELDNET_ROLE_SYNC_MINUTES")
    security_scan_minutes: int = Field(default=15, alias="SHIELDNET_SECURITY_SCAN_MINUTES")
    model_config = SettingsConfigDict(env_file="/etc/shieldnet/scheduler/scheduler.env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()
