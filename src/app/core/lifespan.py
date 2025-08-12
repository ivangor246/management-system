from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.admin.setup import create_admin_if_not_exists
from app.core.database import init_models


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_models()
    await create_admin_if_not_exists()

    yield
