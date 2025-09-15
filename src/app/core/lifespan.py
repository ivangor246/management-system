"""
Application lifespan management.

This module defines an async context manager for FastAPI's lifespan event.
It ensures that database tables are initialized and the admin user is created
before the application starts serving requests.

Functions:
    lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        Async context manager for FastAPI lifespan handling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.admin.setup import create_admin_if_not_exists


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Initializes the admin user if it does not exist

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None
    """
    await create_admin_if_not_exists()

    yield
