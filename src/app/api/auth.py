from typing import Annotated

from fastapi import APIRouter, status

from app.schemas.auth import CredentialsSchema, LogoutSuccessSchema, TokenSchema
from app.services.auth import AuthService, Depends, get_auth_service

auth_router = APIRouter(prefix='/auth', tags=['auth'])


@auth_router.post('/login', status_code=status.HTTP_200_OK)
async def authenticate(
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: CredentialsSchema,
) -> TokenSchema:
    """
    Authenticate a user using email and password.

    Args:
        service (AuthService): The authentication service dependency.
        credentials (CredentialsSchema): User credentials with email and password.

    Returns:
        TokenSchema: JWT access token if authentication is successful.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    return await service.authenticate(credentials)


@auth_router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(
    token: str,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutSuccessSchema:
    """
    Logout user by blacklisting their JWT token.

    Args:
        token (str): JWT token sent in the request.
        service (AuthService): AuthService instance.

    Returns:
        LogoutSuccessSchema: Success message.
    """
    return await service.logout(token)
