import pytest
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.users import UserManager
from app.models.users import User
from app.schemas.users import UserCreateSchema, UserCreateSuccessSchema
from app.services.register import RegisterService


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
class TestRegisterService:
    async def test_register_user(self, session: AsyncSession, user_data: UserCreateSchema):
        manager = UserManager(session)
        service = RegisterService(manager)

        response = await service.register_user(user_data)
        assert isinstance(response, UserCreateSuccessSchema)

        stmt = select(User).where(User.id == response.user_id)
        result = await session.execute(stmt)
        added_user = result.scalar_one()
        assert isinstance(added_user, User)
        assert added_user.username == user_data.username
        assert added_user.email == user_data.email
        assert added_user.hashed_password != user_data.password
        assert added_user.first_name == user_data.first_name
        assert added_user.last_name == user_data.last_name

    async def test_register_user_with_existing_username(self, session: AsyncSession, user_data: UserCreateSchema):
        manager = UserManager(session)
        service = RegisterService(manager)
        await service.register_user(user_data)

        with pytest.raises(HTTPException) as exc_info:
            user_data_copy = user_data.model_copy()
            user_data_copy.email = 'email2@email.com'
            await service.register_user(user_data_copy)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_register_user_with_existing_email(self, session: AsyncSession, user_data: UserCreateSchema):
        manager = UserManager(session)
        service = RegisterService(manager)
        await service.register_user(user_data)

        with pytest.raises(HTTPException) as exc_info:
            user_data_copy = user_data.model_copy()
            user_data_copy.username = 'username2'
            await service.register_user(user_data_copy)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
