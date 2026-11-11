from logging.config import fileConfig
from pathlib import Path
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base
import app.models  # noqa: F401: registra los modelos en Base.metadata.


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def migration_database_url() -> str:
    """Use the dedicated, local-only migration account when configured.

    The application continues to obtain ``DATABASE_URL`` from ``.env``.  This
    keeps DDL credentials out of normal FastAPI execution while allowing
    Alembic to run with the account intended for schema changes.
    """
    configured = os.getenv("MIGRATION_DATABASE_URL")
    if configured:
        return configured

    migration_env = Path(__file__).resolve().parents[1] / ".env.migration"
    if migration_env.exists():
        for line in migration_env.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "MIGRATION_DATABASE_URL":
                return value.strip().strip('"').strip("'")

    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=migration_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = migration_database_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
