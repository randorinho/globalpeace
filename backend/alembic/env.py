import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # /app on the image

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db import Base
from app import models  # noqa: F401 — register all tables

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # PostGIS internals must never be managed by our migrations
    if type_ == "table" and name in ("spatial_ref_sys",):
        return False
    return True


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata,
                      include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


async def run_async():
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    raise SystemExit("offline mode not supported")
asyncio.run(run_async())
