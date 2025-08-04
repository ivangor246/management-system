from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.root import get_root_router
from app.core.config import config
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.TITLE,
        docs_url=config.DOCS_URL,
        openapi_url=config.OPENAPI_URL,
        default_response_class=JSONResponse,
        lifespan=lifespan,
        debug=config.DEBUG,
    )

    root_router = get_root_router()
    app.include_router(root_router)

    return app
