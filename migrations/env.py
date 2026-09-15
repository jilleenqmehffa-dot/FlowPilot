"""Alembic runtime configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, make_url, pool

from backend.app import models  # noqa: F401 -- register models on metadata
from backend.app.core.config import get_settings
from backend.app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_database_url(*, online: bool) -> str:
    database_url = get_settings().database_url
    if database_url is None:
        if online:
            raise RuntimeError("Set DATABASE_URL before running online migrations")
        database_url = config.get_main_option("sqlalchemy.url")

    url = make_url(database_url)
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use postgresql+psycopg://")
    return url.render_as_string(hide_password=False)


def configure_context(**kwargs: object) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    configure_context(
        url=get_database_url(online=False),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        get_database_url(online=True),
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )
    try:
        with connectable.connect() as connection:
            configure_context(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
