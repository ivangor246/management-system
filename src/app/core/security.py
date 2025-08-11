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
    token = credentials.credentials

    token_mixin = TokenMixin()
    payload = token_mixin.validate_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
        )

    email = token_mixin.get_email_form_payload(payload)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token payload',
        )

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
        )

    return user


async def require_user(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    stmt = select(UserTeam).where(
        UserTeam.user_id == user.id,
        UserTeam.team_id == team_id,
    )
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not a member of this team',
        )

    return user


async def require_admin(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    stmt = select(UserTeam).where(
        UserTeam.user_id == user.id,
        UserTeam.team_id == team_id,
    )
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association or association.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required',
        )

    return user


async def require_manager(
    team_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    stmt = select(UserTeam).where(
        UserTeam.user_id == user.id,
        UserTeam.team_id == team_id,
    )
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()

    if not association or association.role not in {UserRoles.MANAGER, UserRoles.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Manager or admin access required',
        )

    return user


class HashingMixin:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(password, hashed_password)
        except UnknownHashError:
            return False


class TokenMixin:
    def generate_access_token(self, email: str) -> str:
        return jwt.encode(
            self.__create_payload(email),
            config.SECRET_KEY,
            algorithm=config.TOKEN_ALGORITHM,
        )

    def validate_token(self, token: str) -> dict | None:
        try:
            payload = self.__decode_access_token(token)
        except Exception:
            return None

        if self.__is_token_expired(payload):
            return None

        return payload

    def get_email_form_payload(self, payload: dict) -> str | None:
        return payload.get('sub')

    def __create_payload(self, email: str) -> dict:
        expires_at = int(datetime.now(timezone.utc).timestamp()) + config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {'sub': email, 'expires_at': expires_at}

    def __decode_access_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.TOKEN_ALGORITHM],
        )

    def __is_token_expired(self, payload: dict) -> bool:
        expires_at = payload.get('expires_at')
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        return current_timestamp > expires_at
