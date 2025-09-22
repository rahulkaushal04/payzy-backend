import sys
from pathlib import Path
from alembic import context
from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config

# Add the project root to Python path
project_root = Path(__file__).parents[1]
sys.path.insert(0, str(project_root))

# Import application settings
from app.core.config import settings
from app.core.database import Base

# Import application models
from app.entity.user import UserEntity

# Alembic Config
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Database URL (ensure asyncpg driver is used)
config.set_main_option("sqlalchemy.url", settings.effective_database_url)

# Target metadata for 'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (SQL script generation).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (apply directly to DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
