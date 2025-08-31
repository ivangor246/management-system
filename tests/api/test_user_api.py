import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import TokenMixin
from app.main import create_app
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.users import UserCreateSchema, UserUpdateSchema


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app()
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
class TestUsersAPI:
    async def _get_token(self, email: str) -> str:
        return TokenMixin().generate_access_token(email)

    async def test_get_user_data(self, app: FastAPI, session: AsyncSession, user_data: UserCreateSchema):
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        token = await self._get_token(user.email)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                '/api/users/me',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['username'] == user_data.username
        assert data['email'] == user_data.email

    async def test_update_user(self, app: FastAPI, session: AsyncSession, user_data: UserCreateSchema):
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        token = await self._get_token(user.email)

        update_data = UserUpdateSchema(
            first_name='Updated',
            last_name='UserUpdated',
            email='updated@email.com',
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.put(
                '/api/users/me',
                json=update_data.model_dump(),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        updated_user = result.scalar_one_or_none()
        assert updated_user.email == update_data.email
        assert updated_user.first_name == update_data.first_name
        assert updated_user.last_name == update_data.last_name

    async def test_delete_user(self, app: FastAPI, session: AsyncSession, user_data: UserCreateSchema):
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        token = await self._get_token(user.email)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.delete(
                '/api/users/me',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None
