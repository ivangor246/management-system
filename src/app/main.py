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
from fastapi.staticfiles import StaticFiles

from app.admin.setup import init_admin
from app.api.root import get_root_router
from app.core.config import config
from app.core.lifespan import lifespan
from app.front.router import front_router


def create_app(skip_static: bool = False) -> FastAPI:
    """
    Creates and configures the FastAPI application.

    The application is configured with:
        - Application title, docs, and OpenAPI URLs from the configuration.
        - Default response class as JSONResponse.
        - Lifespan management for startup/shutdown events.
        - Debug mode as defined in the configuration.
        - Admin interface initialization.
        - Root router inclusion.
        - Frontend routed inclusion.
        - Mount static files (skipped if skip_static=True).

    Args:
        skip_static (bool, optional): If True, the static files directory will not
            be mounted. Defaults to False. Useful for testing environments.

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

    app.include_router(front_router)

    if not skip_static:
        app.mount('/static', StaticFiles(directory='app/front/static'), name='static')

    return app
