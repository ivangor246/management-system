from passlib.context import CryptContext
from passlib.exc import UnknownHashError

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
    def verify_password(hashed_password: str, password: str) -> bool:
        try:
            return pwd_context.verify(password, hashed_password)
        except UnknownHashError:
            return False
