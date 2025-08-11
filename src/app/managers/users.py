from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import HashingMixin
from app.models.users import User
from app.schemas.auth import CredentialsSchema
from app.schemas.users import UserCreateSchema


class UserManager(HashingMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreateSchema) -> User:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        self.session.add(new_user)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

        await self.session.refresh(new_user)
        return new_user

    async def check_user_by_credentials(self, credentials: CredentialsSchema) -> bool:
        stmt = select(User).where(User.email == credentials.email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(credentials.password, user.hashed_password):
            return False

        return True


def get_user_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> UserManager:
    return UserManager(session=session)
