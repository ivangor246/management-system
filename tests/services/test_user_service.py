import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.users import UserManager
from app.models.users import User
from app.schemas.users import UserCreateSchema, UserSchema, UserUpdateSchema, UserUpdateSuccessSchema
from app.services.users import UserService


@pytest.fixture
def user_data():
    return UserCreateSchema(
        username='username1',
        email='email1@email.com',
        password='password1',
        first_name='first_name1',
        last_name='last_name1',
    )


@pytest_asyncio.fixture
async def user(session: AsyncSession, user_data) -> User:
    user_manager = UserManager(session)
    new_user = await user_manager.create_user(user_data)
    return new_user


@pytest.mark.asyncio
class TestUserService:
    async def test_get_user_data(self, session: AsyncSession, user: User):
        manager = UserManager(session)
        service = UserService(manager)

        response = await service.get_user_data(user)

        assert isinstance(response, UserSchema)
        assert response.username == user.username
        assert response.email == user.email
        assert response.first_name == user.first_name
        assert response.last_name == user.last_name
        assert response.is_admin == user.is_admin

    async def test_update_user(self, session: AsyncSession, user: User):
        manager = UserManager(session)
        service = UserService(manager)

        old_hashed_password = user.hashed_password

        user_data_for_update = UserUpdateSchema(
            username='username2',
            email='email2@email.com',
            password='password2',
        )
        response = await service.update_user(user, user_data_for_update)
        assert isinstance(response, UserUpdateSuccessSchema)

        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        updated_user = result.scalar_one()
        assert updated_user.username == user_data_for_update.username
        assert updated_user.email == user_data_for_update.email
        assert updated_user.hashed_password != user_data_for_update.password
        assert updated_user.hashed_password != old_hashed_password

        user_data_for_update = UserUpdateSchema(
            first_name='first_name2',
            last_name='last_name2',
        )
        response = await service.update_user(user, user_data_for_update)
        assert isinstance(response, UserUpdateSuccessSchema)

        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        updated_user = result.scalar_one()
        assert updated_user.first_name == user_data_for_update.first_name
        assert updated_user.last_name == user_data_for_update.last_name

    async def test_update_user_with_existing_username(
        self, session: AsyncSession, user: User, user_data: UserCreateSchema
    ):
        manager = UserManager(session)
        service = UserService(manager)
        user_data_for_update = UserUpdateSchema(username='username2')

        user_data.username = 'username2'
        user_data.email = 'email2@email.com'
        await manager.create_user(user_data)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_user(user, user_data_for_update)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_update_user_with_existing_email(
        self, session: AsyncSession, user: User, user_data: UserCreateSchema
    ):
        manager = UserManager(session)
        service = UserService(manager)
        user_data_for_update = UserUpdateSchema(email='email2@email.com')

        user_data.username = 'username2'
        user_data.email = 'email2@email.com'
        await manager.create_user(user_data)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_user(user, user_data_for_update)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_user(self, session: AsyncSession, user: User):
        manager = UserManager(session)
        service = UserService(manager)

        await service.delete_user(user)

        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None
