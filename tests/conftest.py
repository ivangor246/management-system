from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import config
from app.models.base import Base


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(config.DB_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def clean_database(session: AsyncSession):
    async with session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))

    await session.commit()
