"""
Application factory for creating a FastAPI instance.

This module provides the `create_app` function to initialize and configure
the FastAPI application, including routers, admin setup, and lifespan management.

Functions:
    create_app() -> FastAPI:
        Creates and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.admin.setup import init_admin
from app.api.root import get_root_router
from app.core.config import config
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.

    The application is configured with:
        - Application title, docs, and OpenAPI URLs from the configuration.
        - Default response class as JSONResponse.
        - Lifespan management for startup/shutdown events.
        - Debug mode as defined in the configuration.
        - Admin interface initialization.
        - Root router inclusion.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title=config.TITLE,
        docs_url=config.DOCS_URL,
        openapi_url=config.OPENAPI_URL,
        default_response_class=JSONResponse,
        lifespan=lifespan,
        debug=config.DEBUG,
    )

    init_admin(app)

    root_router = get_root_router()
    app.include_router(root_router)

    return app
