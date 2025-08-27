"""
Database module for asynchronous SQLAlchemy operations.

This module provides the asynchronous engine, session factory, and helper
functions to manage the database schema. It also includes a dependency
for FastAPI to provide sessions to endpoints.

Functions:
    get_session() -> AsyncGenerator[AsyncSession, None]: Async generator yielding a database session.
    init_models() -> None: Initializes all database tables.
    drop_models() -> None: Drops all database tables.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import config
from app.models import Base

engine = create_async_engine(url=config.DB_URL)

session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields a database session.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous session.
    """
    async with session_factory() as session:
        yield session


async def init_models() -> None:
    """
    Initializes all database tables based on SQLAlchemy models.

    This should be run at application startup or during testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_models() -> None:
    """
    Drops all database tables based on SQLAlchemy models.

    This is typically used in testing or resetting the database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
