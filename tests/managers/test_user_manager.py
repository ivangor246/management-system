import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.users import UserManager
from app.models.users import User
from app.schemas.users import UserCreateSchema, UserUpdateSchema


@pytest.fixture
def user_data():
    return UserCreateSchema(
        username='username1',
        email='email1@email.com',
        password='password1',
        first_name='first_name1',
        last_name='last_name1',
    )


@pytest.mark.asyncio
class TestUserManager:
    async def test_create_user(self, session: AsyncSession, user_data: UserCreateSchema):
        manager = UserManager(session)

        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        old_user_count = result.scalar_one()

        new_user = await manager.create_user(user_data)

        assert isinstance(new_user, User)
        assert new_user.username == user_data.username
        assert new_user.email == user_data.email
        assert new_user.first_name == user_data.first_name
        assert new_user.last_name == user_data.last_name
        assert new_user.hashed_password != user_data.password

        with pytest.raises(IntegrityError):
            await manager.create_user(user_data)

        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        new_user_count = result.scalar_one()

        assert new_user_count - old_user_count == 1

    async def test_update_user(self, session: AsyncSession, user_data: UserCreateSchema) -> User:
        manager = UserManager(session)
        user_update_data = UserUpdateSchema(
            username='username2',
            email='email2@email.com',
            password='password2',
            first_name='first_name2',
        )

        new_user = await manager.create_user(user_data)
        old_hashed_password = new_user.hashed_password
        old_last_name = new_user.last_name
        updated_user = await manager.update_user(new_user, user_update_data)

        assert updated_user.username == user_update_data.username
        assert updated_user.email == user_update_data.email
        assert updated_user.hashed_password != old_hashed_password
        assert updated_user.hashed_password != user_update_data.password
        assert updated_user.first_name == user_update_data.first_name
        assert updated_user.last_name == old_last_name

    async def test_delete_user(self, session: AsyncSession, user_data: UserCreateSchema):
        manager = UserManager(session)

        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        old_user_count = result.scalar_one()

        new_user = await manager.create_user(user_data)
        await manager.delete_user(new_user)

        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        new_user_count = result.scalar_one()

        assert new_user_count == old_user_count
