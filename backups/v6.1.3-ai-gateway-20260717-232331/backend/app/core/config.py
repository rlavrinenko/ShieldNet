from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = Field(default="development", alias="SHIELDNET_ENV")
    debug: bool = Field(default=False, alias="SHIELDNET_DEBUG")
    secret_key: str = Field(alias="SHIELDNET_SECRET_KEY")
    internal_service_token: str = Field(alias="SHIELDNET_INTERNAL_SERVICE_TOKEN")
    jwt_algorithm: str = Field(default="HS256", alias="SHIELDNET_JWT_ALGORITHM")
    access_token_minutes: int = Field(default=15, alias="SHIELDNET_ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=30, alias="SHIELDNET_REFRESH_TOKEN_DAYS")

    db_host: str = Field(default="127.0.0.1", alias="SHIELDNET_DB_HOST")
    db_port: int = Field(default=5432, alias="SHIELDNET_DB_PORT")
    db_name: str = Field(default="shieldnet", alias="SHIELDNET_DB_NAME")
    db_user: str = Field(alias="SHIELDNET_DB_USER")
    db_password: str = Field(alias="SHIELDNET_DB_PASSWORD")
    db_pool_size: int = Field(default=10, alias="SHIELDNET_DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="SHIELDNET_DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="SHIELDNET_DB_POOL_TIMEOUT")

    discord_client_id: str = Field(default="", alias="SHIELDNET_DISCORD_CLIENT_ID")
    discord_client_secret: str = Field(default="", alias="SHIELDNET_DISCORD_CLIENT_SECRET")
    discord_redirect_uri: str = Field(default="", alias="SHIELDNET_DISCORD_REDIRECT_URI")
    discord_oauth_scopes: str = Field(default="identify email guilds", alias="SHIELDNET_DISCORD_OAUTH_SCOPES")
    superadmin_ids: str = Field(default="", alias="SHIELDNET_SUPERADMIN_IDS")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="SHIELDNET_REDIS_URL")
    discord_job_queue: str = Field(default="shieldnet:discord:jobs", alias="SHIELDNET_DISCORD_JOB_QUEUE")
    ai_credentials_master_key: str = Field(default="", alias="AI_CREDENTIALS_MASTER_KEY")

    model_config = SettingsConfigDict(
        env_file=(
            "/etc/shieldnet/backend/backend.env",
            "/etc/shieldnet/backend/discord.env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def superadmin_id_set(self) -> set[int]:
        result: set[int] = set()
        for raw in self.superadmin_ids.replace(";", ",").split(","):
            value = raw.strip()
            if not value:
                continue
            try:
                result.add(int(value))
            except ValueError:
                continue
        return result

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.db_user)}:"
            f"{quote_plus(self.db_password)}@{self.db_host}:"
            f"{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
