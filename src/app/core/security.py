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
    def generate_access_token(self, username: str) -> str:
        return jwt.encode(
            self.__create_payload(username),
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

    def get_username_form_payload(self, payload: dict) -> str | None:
        return payload.get('sub')

    def __create_payload(self, username: str) -> dict:
        expires_at = int(datetime.now(timezone.utc).timestamp()) + config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {'sub': username, 'expires_at': expires_at}

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
