from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import TokenMixin
from app.managers.users import UserManager, get_user_manager
from app.schemas.auth import CredentialsSchema, TokenSchema


class AuthService(TokenMixin):
    def __init__(self, manager: UserManager):
        self.manager = manager

    async def authenticate(self, credentials: CredentialsSchema) -> TokenSchema:
        is_user_exists = await self.manager.check_user_by_credentials(credentials)

        if not is_user_exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password',
            )

        access_token = self.generate_access_token(username=credentials.username)
        return TokenSchema(access_token=access_token)


def get_auth_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> AuthService:
    return AuthService(manager=manager)
