from datetime import date

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.main import create_app
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.teams import TeamCreateSchema, UserRoles, UserTeamCreateSchema


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app()
    new_app.dependency_overrides[get_session] = lambda: session
    return new_app


@pytest.fixture
def user_data():
    from app.schemas.users import UserCreateSchema

    return UserCreateSchema(
        username='testuser',
        email='testuser@email.com',
        password='password123',
        first_name='Test',
        last_name='User',
    )


@pytest.mark.asyncio
class TestTeamsAPI:
    async def _create_user_and_token(self, session: AsyncSession, user_data) -> tuple[User, str]:
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        from app.core.security import TokenMixin

        token = TokenMixin().generate_access_token(user.email)
        return user, token

    async def test_create_team(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team_data = TeamCreateSchema(name='Test Team')

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                '/api/teams/',
                json=team_data.model_dump(),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'team_id' in response.json()

    async def test_get_my_teams(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team_manager = TeamManager(session)
        await team_manager.create_team(TeamCreateSchema(name='Team 1'), user)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                '/api/teams/',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]['role'] is not None

    async def test_add_team_member(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, manager_token = await self._create_user_and_token(session, user_data)
        team_manager = TeamManager(session)
        team = await team_manager.create_team(TeamCreateSchema(name='Team 1'), manager_user)

        user_team_data = UserTeamCreateSchema(
            user_id=manager_user.id,
            role=UserRoles.USER,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                f'/api/teams/{team.id}/users',
                json=user_team_data.model_dump(),
                headers={'Authorization': f'Bearer {manager_token}'},
            )

        assert response.status_code == status.HTTP_200_OK

    async def test_remove_team_member(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, manager_token = await self._create_user_and_token(session, user_data)
        team_manager = TeamManager(session)
        team = await team_manager.create_team(TeamCreateSchema(name='Team 1'), manager_user)
        await team_manager.assign_role(manager_user.id, team.id, UserRoles.ADMIN)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.delete(
                f'/api/teams/{team.id}/users/{manager_user.id}',
                headers={'Authorization': f'Bearer {manager_token}'},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_get_avg_evaluation(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team_manager = TeamManager(session)
        team = await team_manager.create_team(TeamCreateSchema(name='Team 1'), user)
        await team_manager.assign_role(user.id, team.id, UserRoles.USER)

        start_date = date.today()
        end_date = date.today()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/avg-evaluation?start_date={start_date}&end_date={end_date}',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
