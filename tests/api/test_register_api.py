import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.main import create_app
from app.models.users import User
from app.schemas.users import UserCreateSchema


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app()
    new_app.dependency_overrides[get_session] = lambda: session
    return new_app


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
class TestRegisterAPI:
    async def test_register_user(self, app: FastAPI, session: AsyncSession, user_data: UserCreateSchema):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                '/api/auth/register',
                json=user_data.model_dump(),
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'user_id' in data
        assert isinstance(data['user_id'], int)

        stmt = select(User).where(User.email == user_data.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.username == user_data.username

    async def test_register_user_conflict(self, app: FastAPI, user_data: UserCreateSchema):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            first_response = await ac.post(
                '/api/auth/register',
                json=user_data.model_dump(),
            )
            assert first_response.status_code == status.HTTP_201_CREATED

            second_response = await ac.post(
                '/api/auth/register',
                json=user_data.model_dump(),
            )

            assert second_response.status_code == status.HTTP_400_BAD_REQUEST
