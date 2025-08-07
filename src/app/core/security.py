from datetime import datetime, timezone

import jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.core.config import config

pwd_context = CryptContext(
    schemes=['argon2'],
    deprecated='auto',
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=4,
)


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
    @staticmethod
    def generate_access_token(username: int) -> str:
        return jwt.encode(TokenMixin.__create_payload(username), config.SECRET_KEY, algorithm=config.TOKEN_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.TOKEN_ALGORITHM])

    @staticmethod
    def __create_payload(username: int) -> dict:
        expires_at = int(datetime.now(timezone.utc).timestamp()) + config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {'sub': username, 'expires_at': expires_at}
