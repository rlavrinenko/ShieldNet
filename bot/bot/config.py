from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    discord_bot_token: str = Field(alias="SHIELDNET_DISCORD_BOT_TOKEN")
    discord_application_id: int = Field(alias="SHIELDNET_DISCORD_APPLICATION_ID")
    backend_url: str = Field(default="http://127.0.0.1:8000", alias="SHIELDNET_BACKEND_URL")
    internal_service_token: str = Field(alias="SHIELDNET_INTERNAL_SERVICE_TOKEN")
    default_language: str = Field(default="uk", alias="SHIELDNET_DEFAULT_LANGUAGE")
    sync_commands_on_start: bool = Field(default=True, alias="SHIELDNET_SYNC_COMMANDS_ON_START")
    log_level: str = Field(default="INFO", alias="SHIELDNET_LOG_LEVEL")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="SHIELDNET_REDIS_URL")
    worker_queue: str = Field(default="shieldnet:discord:jobs", alias="SHIELDNET_WORKER_QUEUE")
    heartbeat_seconds: int = Field(default=30, alias="SHIELDNET_HEARTBEAT_SECONDS")
    model_config = SettingsConfigDict(
        env_file="/etc/shieldnet/bot/bot.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
