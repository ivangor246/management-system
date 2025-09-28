from datetime import date, time, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.meetings import MeetingManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.meetings import Meeting
from app.models.teams import Team
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema, MeetingUpdateSchema
from app.schemas.teams import TeamCreateSchema
from app.schemas.users import UserCreateSchema
from app.services.meetings import MeetingService


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
    manager = UserManager(session)
    return await manager.create_user(user_data)


@pytest.fixture
def team_data():
    return TeamCreateSchema(
        name='team_name1',
        description='description1',
    )


@pytest_asyncio.fixture
async def team(session: AsyncSession, user: User, team_data) -> Team:
    manager = TeamManager(session)
    return await manager.create_team(team_data, user)


@pytest_asyncio.fixture
async def meeting(session: AsyncSession, team: Team, user: User) -> Meeting:
    manager = MeetingManager(session)
    meeting_data = MeetingCreateSchema(
        name='meeting_name1',
        date=date.today() + timedelta(days=5),
        time=time(hour=10, minute=0),
        member_ids=[user.id],
    )
    meeting = await manager.create_meeting(meeting_data, team.id)
    return meeting


@pytest.mark.asyncio
class TestMeetingService:
    async def test_create_meeting(self, session: AsyncSession, team: Team, user: User):
        manager = MeetingManager(session)
        service = MeetingService(manager)
        meeting_data = MeetingCreateSchema(
            name='meeting_name2',
            date=date.today() + timedelta(days=6),
            time=time(hour=11, minute=0),
            member_ids=[user.id],
        )
        result = await service.create_meeting(meeting_data, team.id)
        assert result.meeting_id is not None

    async def test_get_meetings_by_team(self, session: AsyncSession, team: Team, meeting: Meeting):
        manager = MeetingManager(session)
        service = MeetingService(manager)
        meetings = await service.get_meetings_by_team(team.id)
        assert any(m.id == meeting.id for m in meetings)

    async def test_get_meetings_by_member(self, session: AsyncSession, team: Team, meeting: Meeting, user: User):
        manager = MeetingManager(session)
        service = MeetingService(manager)
        meetings = await service.get_meetings_by_member(user.id, team.id)
        assert any(m.id == meeting.id for m in meetings)

    async def test_update_meeting(self, session: AsyncSession, meeting: Meeting, team: Team, user: User):
        manager = MeetingManager(session)
        service = MeetingService(manager)
        update_data = MeetingUpdateSchema(
            name='meeting_name_updated',
            member_ids=[user.id],
        )
        result = await service.update_meeting(update_data, meeting.id, team.id)
        assert result.detail == 'The meeting has been successfully updated'

    async def test_delete_meeting(self, session: AsyncSession, meeting: Meeting):
        manager = MeetingManager(session)
        service = MeetingService(manager)
        await service.delete_meeting(meeting.id, meeting.team_id)
        meetings = await service.manager.get_meetings_by_team(meeting.team_id)
        assert meeting.id not in [m.id for m in meetings]
