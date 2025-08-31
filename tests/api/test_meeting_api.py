from datetime import date, time, timedelta

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import TokenMixin
from app.main import create_app
from app.managers.meetings import MeetingManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema, MeetingUpdateSchema
from app.schemas.teams import TeamCreateSchema, UserRoles
from app.schemas.users import UserCreateSchema


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app()
    new_app.dependency_overrides[get_session] = lambda: session
    return new_app


@pytest.fixture
def user_data():
    return UserCreateSchema(
        username='testuser',
        email='testuser@email.com',
        password='password123',
        first_name='Test',
        last_name='User',
    )


@pytest.mark.asyncio
class TestMeetingsAPI:
    async def _create_user_and_token(self, session: AsyncSession, user_data) -> tuple[User, str]:
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        token = TokenMixin().generate_access_token(user.email)
        return user, token

    async def _create_team_with_manager(self, session: AsyncSession, manager_user: User):
        team_manager = TeamManager(session)
        team = await team_manager.create_team(TeamCreateSchema(name='Test Team'), manager_user)
        await team_manager.assign_role(manager_user.id, team.id, UserRoles.MANAGER)
        return team

    async def test_create_meeting(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)

        meeting_data = MeetingCreateSchema(
            name='Team Sync',
            date=date.today() + timedelta(days=1),
            time=time(hour=10, minute=0),
            member_ids=[manager_user.id],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                f'/api/teams/{team.id}/meetings/',
                json=meeting_data.model_dump(mode='json'),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'meeting_id' in response.json()

    async def test_get_meetings_by_team(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        meeting_manager = MeetingManager(session)
        await meeting_manager.create_meeting(
            MeetingCreateSchema(
                name='Team Kickoff', date=date.today(), time=time(hour=9, minute=0), member_ids=[manager_user.id]
            ),
            team.id,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/meetings/',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]['name'] == 'Team Kickoff'

    async def test_get_my_meetings_in_team(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        meeting_manager = MeetingManager(session)
        await meeting_manager.create_meeting(
            MeetingCreateSchema(
                name='One-on-One', date=date.today(), time=time(hour=11, minute=0), member_ids=[manager_user.id]
            ),
            team.id,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/meetings/mine',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert manager_user.id == data[0]['users'][0]['id']

    async def test_update_meeting(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        meeting_manager = MeetingManager(session)
        meeting = await meeting_manager.create_meeting(
            MeetingCreateSchema(
                name='Daily Standup', date=date.today(), time=time(hour=9, minute=0), member_ids=[manager_user.id]
            ),
            team.id,
        )

        meeting_update = MeetingUpdateSchema(name='Updated Standup')

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.put(
                f'/api/teams/{team.id}/meetings/{meeting.id}',
                json=meeting_update.model_dump(mode='json', exclude_unset=True),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['detail'] == 'The meeting has been successfully updated'

    async def test_delete_meeting(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        meeting_manager = MeetingManager(session)
        meeting = await meeting_manager.create_meeting(
            MeetingCreateSchema(
                name='Retro', date=date.today(), time=time(hour=15, minute=0), member_ids=[manager_user.id]
            ),
            team.id,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.delete(
                f'/api/teams/{team.id}/meetings/{meeting.id}',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT
