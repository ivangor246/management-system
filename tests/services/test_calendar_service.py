import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.meetings import MeetingManager
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.meetings import Meeting
from app.models.tasks import Task
from app.models.teams import Team
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema
from app.schemas.tasks import TaskCreateSchema
from app.schemas.teams import TeamCreateSchema
from app.schemas.users import UserCreateSchema
from app.services.calendar import CalendarService


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    user_data = UserCreateSchema(
        username='username1',
        email='email1@email.com',
        password='password1',
        first_name='first_name1',
        last_name='last_name1',
    )
    manager = UserManager(session)
    return await manager.create_user(user_data)


@pytest_asyncio.fixture
async def team(session: AsyncSession, user: User) -> Team:
    team_data = TeamCreateSchema(name='team_name1')
    manager = TeamManager(session)
    return await manager.create_team(team_data, user)


@pytest_asyncio.fixture
async def task(session: AsyncSession, team: Team) -> Task:
    task_data = TaskCreateSchema(
        description='task_description1',
        deadline=datetime.date.today(),
        performer_id=None,
        team_id=team.id,
    )
    manager = TaskManager(session)
    return await manager.create_task(task_data, team.id)


@pytest_asyncio.fixture
async def meeting(session: AsyncSession, user: User, team: Team) -> Meeting:
    meeting_data = MeetingCreateSchema(
        name='meeting_name1',
        date=datetime.date.today(),
        time=datetime.datetime.now().time(),
        member_ids=[user.id],
    )
    manager = MeetingManager(session)
    return await manager.create_meeting(meeting_data, team.id)


@pytest.mark.asyncio
class TestCalendarService:
    async def test_get_calendar_by_date(self, session: AsyncSession, team: Team, task: Task, meeting: Meeting):
        service = CalendarService(TaskManager(session), MeetingManager(session))

        result = await service.get_calendar_by_date(team.id, date=datetime.date.today())

        task_events = [e for e in result.events if e.__class__.__name__ == 'TaskSchema']
        meeting_events = [e for e in result.events if e.__class__.__name__ == 'MeetingSchema']

        assert len(task_events) == 1
        assert task_events[0].id == task.id

        assert len(meeting_events) == 1
        assert meeting_events[0].id == meeting.id

    async def test_get_calendar_by_month(self, session: AsyncSession, team: Team, task: Task, meeting: Meeting):
        service = CalendarService(TaskManager(session), MeetingManager(session))

        today = datetime.date.today()
        result = await service.get_calendar_by_month(team.id, year=today.year, month=today.month)

        task_events = [e for e in result.events if e.__class__.__name__ == 'TaskSchema']
        meeting_events = [e for e in result.events if e.__class__.__name__ == 'MeetingSchema']

        assert len(task_events) == 1
        assert task_events[0].id == task.id

        assert len(meeting_events) == 1
        assert meeting_events[0].id == meeting.id
