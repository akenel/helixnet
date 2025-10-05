# migrations/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. SETUP PATHS AND IMPORTS
# This is crucial for Alembic to be able to find and import modules
# from your application when running inside the container.
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import your settings and SQLAlchemy components
from app.core.config import get_settings
from app.db.database import Base  # Assuming Base is defined here

# 🔑 CRITICAL FIX FOR TABLE DISCOVERY:
# The issue is likely that Base.metadata doesn't know about the tables.
# We must explicitly import the modules that define the SQLAlchemy models
# to ensure they are registered with Base.metadata.
# Assuming you have an 'user' model file inside the 'app.db.models' package:
from app.db.models import user

# Add imports for all other model files (e.g., job, task) here!

# This is the target for the models (Base.metadata)
target_metadata = Base.metadata

# other Alembic configuration setup...
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # --- CRITICAL FIX START ---
    # 1. Get the computed URL from the application settings
    settings = get_settings()
    # Use the synchronous URL for Alembic/psycopg
    connectable_url = settings.POSTGRES_SYNC_URL

    # 2. Inject the computed URL directly into the Alembic configuration context
    # This overrides any sqlalchemy.url setting in alembic.ini
    connectable = engine_from_config(
        {"sqlalchemy.url": connectable_url},  # Pass URL directly
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # --- CRITICAL FIX END ---

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Set this if you use the schema parameter in your models, e.g., schema='public'
            # include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline() -> None:
    # Standard Alembic offline logic...
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
