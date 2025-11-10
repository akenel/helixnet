from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path

# --- 1. Path Setup and Imports ---
# Ensure the project root is on the Python path so app imports work inside containers.
# This points sys.path to the directory above 'alembic'.
sys.path.append(str(Path(__file__).resolve().parents[1]))
# Import your settings and SQLAlchemy Base
from src.core.config import get_settings
from src.db.database import Base

# This is the target for the models (Base.metadata)
target_metadata = Base.metadata
# other Alembic configuration setup...
config = context.config
# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # 1. Get the computed URL from the application settings
    settings = get_settings()
    # Use the synchronous URL for Alembic/psycopg
    connectable_url = settings.POSTGRES_SYNC_URI

    # 2. Inject the computed URL directly into the Alembic configuration context
    connectable = engine_from_config(
        {"sqlalchemy.url": connectable_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline() -> None:
    # Standard Alembic offline logic...
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=False,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
