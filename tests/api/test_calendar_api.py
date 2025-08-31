from datetime import date, time

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import TokenMixin
from app.main import create_app
from app.managers.meetings import MeetingManager
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema
from app.schemas.tasks import TaskCreateSchema
from app.schemas.teams import TeamCreateSchema, UserRoles
from app.schemas.users import UserCreateSchema


@pytest.fixture
def user_data():
    return UserCreateSchema(
        username='testuser',
        email='testuser@email.com',
        password='password123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    new_app = create_app()
    new_app.dependency_overrides[get_session] = lambda: session
    return new_app


@pytest.mark.asyncio
class TestCalendarAPI:
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

    async def _create_task(self, session: AsyncSession, team_id: int, description='Calendar Task', deadline=None):
        task_manager = TaskManager(session)
        task = await task_manager.create_task(
            TaskCreateSchema(description=description, deadline=deadline or date.today()), team_id
        )
        return task

    async def _create_meeting(self, session: AsyncSession, team_id: int, meeting_date=None):
        meeting_manager = MeetingManager(session)
        meeting = await meeting_manager.create_meeting(
            MeetingCreateSchema(
                name='Calendar Meeting',
                date=meeting_date or date.today(),
                time=time(hour=10, minute=0),
                member_ids=[],
            ),
            team_id,
        )
        return meeting

    async def test_get_calendar_by_date(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, user)
        await self._create_task(session, team.id, deadline=date.today())
        await self._create_meeting(session, team.id, meeting_date=date.today())

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/calendar/date',
                params={'date': str(date.today())},
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['date'] == str(date.today())
        event_types = [event.get('description', None) or event.get('name', None) for event in data['events']]
        assert 'Calendar Task' in event_types
        assert 'Calendar Meeting' in event_types

    async def test_get_calendar_by_month(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, user)
        today = date.today()
        await self._create_task(session, team.id, deadline=today)
        await self._create_meeting(session, team.id, meeting_date=today)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/calendar/month',
                params={'year': today.year, 'month': today.month},
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['year'] == today.year
        assert data['month'] == today.month
        event_types = [event.get('description', None) or event.get('name', None) for event in data['events']]
        assert 'Calendar Task' in event_types
        assert 'Calendar Meeting' in event_types
