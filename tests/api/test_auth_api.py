import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.main import create_app
from app.managers.users import UserManager
from app.schemas.auth import CredentialsSchema
from app.schemas.users import UserCreateSchema


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app(skip_static=True)
    new_app.dependency_overrides[get_session] = lambda: session
    return new_app


@pytest.fixture
def user_data() -> UserCreateSchema:
    return UserCreateSchema(
        username='testuser',
        email='testuser@email.com',
        password='password123',
        first_name='Test',
        last_name='User',
    )


@pytest.mark.asyncio
class TestAuthAPI:
    async def test_login_success(self, app: FastAPI, session: AsyncSession, user_data: UserCreateSchema):
        user_manager = UserManager(session)
        await user_manager.create_user(user_data)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                '/api/auth/login',
                json=CredentialsSchema(
                    email=user_data.email,
                    password=user_data.password,
                ).model_dump(),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access_token' in data
        assert isinstance(data['access_token'], str)

    async def test_login_invalid_credentials(self, app: FastAPI, user_data: UserCreateSchema):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                '/api/auth/login',
                json=CredentialsSchema(
                    email=user_data.email,
                    password='wrongpassword',
                ).model_dump(),
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data['detail'] == 'Invalid username or password'
