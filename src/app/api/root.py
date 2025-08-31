from fastapi import APIRouter

from .auth import auth_router
from .register import register_router
from .teams import teams_router
from .users import users_router

ROUTERS = [
    auth_router,
    register_router,
    teams_router,
    users_router,
]


def get_root_router() -> APIRouter:
    """
    Creates the root API router and includes all sub-routers.

    Returns:
        APIRouter: Root router with all API routes included.
    """
    root_router = APIRouter(prefix='/api')

    for router in ROUTERS:
        root_router.include_router(router)

    return root_router
