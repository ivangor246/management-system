from typing import Annotated

from fastapi import APIRouter, status

from app.schemas.auth import CredentialsSchema, TokenSchema
from app.services.auth import AuthService, Depends, get_auth_service

auth_router = APIRouter(prefix='/auth', tags=['auth'])


@auth_router.post('/login', status_code=status.HTTP_200_OK)
async def authenticate(
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: CredentialsSchema,
) -> TokenSchema:
    return await service.authenticate(credentials)
