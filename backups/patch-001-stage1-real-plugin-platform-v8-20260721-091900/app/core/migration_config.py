from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MigrationSettings(BaseSettings):
    db_host: str = Field(alias="SHIELDNET_MIGRATION_DB_HOST")
    db_port: int = Field(alias="SHIELDNET_MIGRATION_DB_PORT")
    db_name: str = Field(alias="SHIELDNET_MIGRATION_DB_NAME")
    db_user: str = Field(alias="SHIELDNET_MIGRATION_DB_USER")
    db_password: str = Field(alias="SHIELDNET_MIGRATION_DB_PASSWORD")

    model_config = SettingsConfigDict(
        env_file="/etc/shieldnet/backend/migrations.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_migration_settings() -> MigrationSettings:
    return MigrationSettings()


migration_settings = get_migration_settings()
