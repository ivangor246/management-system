"""
Authentication and security utilities.

This module provides dependencies and mixins for FastAPI applications
to handle user authentication, role-based access control, password hashing,
and JWT token generation/validation.

Dependencies:
    get_request_user: Retrieves the currently authenticated user from the JWT token.
    require_user: Ensures the user is a member of a given team.
    require_admin: Ensures the user is an admin of a given team.
    require_manager: Ensures the user is a manager or admin of a given team.

Mixins:
    HashingMixin: Provides password hashing and verification using Argon2.
    TokenMixin: Provides JWT token creation, validation, and payload extraction.
"""

from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.database import get_session
from app.models.teams import UserRoles, UserTeam
from app.models.users import User

http_bearer = HTTPBearer()

pwd_context = CryptContext(
    schemes=['argon2'],
    deprecated='auto',
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=4,
)


async def get_request_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Dependency to get the currently authenticated user from a JWT token.

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from the request header.
        session (AsyncSession): Database session.

    Raises:
        HTTPException: If token is invalid, expired, or user does not exist.

    Returns:
        User: The authenticated user.
    """
    token = credentials.credentials
    token_mixin = TokenMixin()
    payload = token_mixin.validate_token(token)

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

    email = token_mixin.get_email_form_payload(payload)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user


async def require_user(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Ensures the authenticated user is a member of a given team.

    Raises:
        HTTPException: If the user is not a team member.

    Returns:
        User: The authenticated user.
    """
    stmt = select(UserTeam).where(UserTeam.user_id == user.id, UserTeam.team_id == team_id)
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not a member of this team')

    return user


async def require_admin(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Ensures the authenticated user is an admin of a given team.

    Raises:
        HTTPException: If the user is not an admin.

    Returns:
        User: The authenticated user.
    """
    stmt = select(UserTeam).where(UserTeam.user_id == user.id, UserTeam.team_id == team_id)
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association or association.role != UserRoles.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required')

    return user


async def require_manager(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Ensures the authenticated user is a manager or admin of a given team.

    Raises:
        HTTPException: If the user is neither manager nor admin.

    Returns:
        User: The authenticated user.
    """
    stmt = select(UserTeam).where(UserTeam.user_id == user.id, UserTeam.team_id == team_id)
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association or association.role not in {UserRoles.MANAGER, UserRoles.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Manager or admin access required')

    return user


class HashingMixin:
    """
    Provides password hashing and verification using Argon2.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hashed password."""
        try:
            return pwd_context.verify(password, hashed_password)
        except UnknownHashError:
            return False


class TokenMixin:
    """
    Provides JWT token generation, validation, and payload extraction.
    """

    def generate_access_token(self, email: str) -> str:
        """
        Generate a JWT access token for a given email.

        Args:
            email (str): User email.

        Returns:
            str: JWT token.
        """
        return jwt.encode(self.__create_payload(email), config.SECRET_KEY, algorithm=config.TOKEN_ALGORITHM)

    def validate_token(self, token: str) -> dict | None:
        """
        Validate a JWT token and return its payload if valid.

        Args:
            token (str): JWT token.

        Returns:
            dict | None: Decoded payload if valid, otherwise None.
        """
        try:
            payload = self.__decode_access_token(token)
        except Exception:
            return None

        if self.__is_token_expired(payload):
            return None

        return payload

    def get_email_form_payload(self, payload: dict) -> str | None:
        """
        Extract the email (subject) from the token payload.

        Args:
            payload (dict): JWT token payload.

        Returns:
            str | None: Email address.
        """
        return payload.get('sub')

    def __create_payload(self, email: str) -> dict:
        """Create JWT payload with email and expiration."""
        expires_at = int(datetime.now(timezone.utc).timestamp()) + config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {'sub': email, 'expires_at': expires_at}

    def __decode_access_token(self, token: str) -> dict:
        """Decode a JWT token."""
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.TOKEN_ALGORITHM])

    def __is_token_expired(self, payload: dict) -> bool:
        """Check if a JWT token is expired."""
        expires_at = payload.get('expires_at')
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        return current_timestamp > expires_at
