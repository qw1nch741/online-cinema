import os
import sys

# 1. Modify the system paths FIRST so Python knows where 'src' is
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# 2. Now you can safely import your project modules
import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import get_settings
from src.database import models  # Force registration of metadata tables
from src.database.session import Base

# This is the Alembic Config object, which provides access to the .ini file values.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide Alembic access to our database schema models catalog
target_metadata = Base.metadata

# Overwrite connection URL dynamically using Pydantic settings config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.ASYNC_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (Generates raw SQL text scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Target function executed synchronously within the async engine connection context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async connection stream."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Wrap our synchronous execution function inside the active async socket
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())