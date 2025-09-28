import time
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.redis import redis
from app.core.security import TokenMixin
from app.managers.users import UserManager, get_user_manager
from app.schemas.auth import CredentialsSchema, LogoutSuccessSchema, TokenSchema


class AuthService(TokenMixin):
    """
    Service responsible for user authentication, JWT token management, and logout functionality.
    """

    def __init__(self, manager: UserManager):
        """
        Initialize AuthService with UserManager and Redis client.

        Args:
            manager (UserManager): Manager for user-related operations.
        """
        self.manager = manager
        self.redis: Redis = redis

    async def authenticate(self, credentials: CredentialsSchema) -> TokenSchema:
        """
        Authenticate a user and generate an access token.

        Args:
            credentials (CredentialsSchema): User credentials containing email and password.

        Returns:
            TokenSchema: Schema containing the generated JWT access token.

        Raises:
            HTTPException: If authentication fails (401 Unauthorized).
        """
        is_user_exists = await self.manager.check_user_by_credentials(credentials)

        if not is_user_exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password',
            )

        access_token = self.generate_access_token(email=credentials.email)
        return TokenSchema(access_token=access_token)

    async def logout(self, access_token: str) -> LogoutSuccessSchema:
        """
        Invalidate a JWT token by blacklisting it in Redis.

        Args:
            access_token (str): The JWT access token to blacklist.

        Returns:
            LogoutSuccessSchema: Schema with a success message.

        Raises:
            HTTPException: If the token is invalid or expired.
        """
        try:
            payload = self.decode_access_token(access_token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token already expired',
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token',
            )

        expires_at = payload.get('expires_at')
        if not expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid token payload',
            )

        ttl = expires_at - int(time.time())
        if ttl <= 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token already expired',
            )

        await self.redis.setex(f'bl:{access_token}', ttl, '1')

        return LogoutSuccessSchema()


def get_auth_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> AuthService:
    """
    Dependency provider for AuthService.

    Args:
        manager (UserManager): Injected UserManager instance.

    Returns:
        AuthService: Initialized AuthService instance.
    """
    return AuthService(manager=manager)
