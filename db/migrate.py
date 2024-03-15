"""
数据库迁移
"""

import asyncio

from application import settings
from core.utils import import_modules
from db.database import async_engine, Base


import_modules(settings.MIGRATE_MODELS, "数据库迁移")


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_tables())
