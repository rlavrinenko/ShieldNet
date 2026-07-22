from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.migration_config import migration_settings
from app.db.base import Base
import app.models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", migration_settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
        version_table="alembic_version",
        version_table_schema="system",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # SHIELDNET_ALEMBIC_VERSION_COLUMN_AUTOFIX_START
        # Ensure descriptive ShieldNet revision IDs fit in Alembic's version table.
        connection.exec_driver_sql(
            "ALTER TABLE IF EXISTS system.alembic_version "
            "ALTER COLUMN version_num TYPE VARCHAR(128)"
        )
        # SHIELDNET_ALEMBIC_VERSION_COLUMN_AUTOFIX_END

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            compare_server_default=True,
            version_table="alembic_version",
            version_table_schema="system",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
