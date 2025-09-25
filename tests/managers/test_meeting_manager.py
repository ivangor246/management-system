import datetime

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.meetings import MeetingManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.meetings import Meeting
from app.models.teams import Team, UserRoles
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema, MeetingUpdateSchema
from app.schemas.teams import TeamCreateSchema
from app.schemas.users import UserCreateSchema


@pytest_asyncio.fixture
async def users(session: AsyncSession) -> list[User]:
    user_manager = UserManager(session)
    users = []
    for i in range(3):
        user_data = UserCreateSchema(
            username=f'username{i}',
            email=f'email{i}@email.com',
            password=f'password{i}',
            first_name=f'first_name{i}',
            last_name=f'last_name{i}',
        )
        new_user = await user_manager.create_user(user_data)
        users.append(new_user)
    return users


@pytest_asyncio.fixture
async def team(session: AsyncSession, users: list[User]) -> Team:
    team_manager = TeamManager(session)
    team_data = TeamCreateSchema(name='team_name1')
    new_team = await team_manager.create_team(team_data, users[0])
    await team_manager.assign_role(users[1].id, new_team.id, UserRoles.MANAGER)
    await team_manager.assign_role(users[2].id, new_team.id, UserRoles.USER)
    return new_team


@pytest.fixture
def meeting_data(users: list[User]) -> MeetingCreateSchema:
    return MeetingCreateSchema(
        name='meeting_name1',
        date=datetime.date.today() + datetime.timedelta(days=5),
        time=datetime.datetime.now().time(),
        member_ids=[users[0].id],
    )


@pytest.mark.asyncio
class TestMeetingManager:
    async def test_create_meeting(
        self, session: AsyncSession, meeting_data: MeetingCreateSchema, users: list[User], team: Team
    ):
        manager = MeetingManager(session)

        new_meeting = await manager.create_meeting(meeting_data, team.id)

        assert isinstance(new_meeting, Meeting)
        assert new_meeting.name == meeting_data.name
        assert new_meeting.date == meeting_data.date
        assert new_meeting.time == meeting_data.time

        with pytest.raises(ValueError):
            await manager.create_meeting(meeting_data, team.id)

        meeting_data_2 = meeting_data.model_copy()
        meeting_data_2.date = meeting_data.date - datetime.timedelta(days=1)
        meeting_data_2.member_ids = [users[1].id, users[2].id]
        new_meeting_2 = await manager.create_meeting(meeting_data_2, team.id)
        assert new_meeting_2.date == meeting_data_2.date
        assert len(new_meeting_2.users) == 2

        stmt = select(func.count()).select_from(Meeting).where(Meeting.team_id == team.id)
        result = await session.execute(stmt)
        meeting_in_team_count = result.scalar_one()
        assert meeting_in_team_count == 2

    async def test_get_meetings_by_team(
        self, session: AsyncSession, meeting_data: MeetingCreateSchema, users: list[User], team: Team
    ):
        manager = MeetingManager(session)
        await manager.create_meeting(meeting_data, team.id)
        meeting_data_2 = meeting_data.model_copy()
        meeting_data_2.date = meeting_data.date - datetime.timedelta(days=1)
        await manager.create_meeting(meeting_data_2, team.id)

        meetings = await manager.get_meetings_by_team(team.id)

        assert len(meetings) == 2
        assert isinstance(meetings[0], Meeting)
        assert meetings[0].team_id == team.id
        assert meetings[1].team_id == team.id

    async def test_get_meetings_by_member(
        self, session: AsyncSession, meeting_data: MeetingCreateSchema, users: list[User], team: Team
    ):
        manager = MeetingManager(session)
        meeting_data.member_ids = [users[1].id]
        await manager.create_meeting(meeting_data, team.id)
        meeting_data_2 = meeting_data.model_copy()
        meeting_data_2.member_ids = [users[1].id, users[2].id]
        meeting_data_2.date = meeting_data.date - datetime.timedelta(days=1)
        await manager.create_meeting(meeting_data_2, team.id)

        meetings = await manager.get_meetings_by_member(users[1].id, team.id)

        assert len(meetings) == 2
        assert isinstance(meetings[0], Meeting)
        assert meetings[0].team_id == team.id
        assert meetings[1].team_id == team.id
        assert users[1] in meetings[0].users
        assert users[1] in meetings[1].users

    async def test_update_meeting(
        self, session: AsyncSession, meeting_data: MeetingCreateSchema, users: list[User], team: Team
    ):
        manager = MeetingManager(session)
        new_meeting = await manager.create_meeting(meeting_data, team.id)

        meeting_data_for_update = MeetingUpdateSchema(
            name='meeting_name2',
            date=meeting_data.date - datetime.timedelta(days=1),
        )
        updated_meeting = await manager.update_meeting(meeting_data_for_update, new_meeting.id, team.id)
        assert updated_meeting.name == meeting_data_for_update.name
        assert updated_meeting.date == meeting_data_for_update.date

        meeting_data_for_update = MeetingUpdateSchema(
            time=(datetime.datetime.now() - datetime.timedelta(hours=1)).time(),
            member_ids=[users[1].id, users[2].id],
        )
        updated_meeting = await manager.update_meeting(meeting_data_for_update, new_meeting.id, team.id)
        assert updated_meeting.time == meeting_data_for_update.time
        assert len(updated_meeting.users) == 2

    async def test_delete_meeting(
        self, session: AsyncSession, meeting_data: MeetingCreateSchema, users: list[User], team: Team
    ):
        manager = MeetingManager(session)
        new_meeting_1 = await manager.create_meeting(meeting_data, team.id)
        meeting_data_2 = meeting_data.model_copy()
        meeting_data_2.date = meeting_data.date - datetime.timedelta(days=1)
        new_meeting_2 = await manager.create_meeting(meeting_data_2, team.id)

        await manager.delete_meeting(new_meeting_1.id, team.id)
        meetings = await manager.get_meetings_by_team(team.id)
        assert len(meetings) == 1

        await manager.delete_meeting(new_meeting_2.id, team.id)
        meetings = await manager.get_meetings_by_team(team.id)
        assert len(meetings) == 0
