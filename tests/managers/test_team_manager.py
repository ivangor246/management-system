from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.evaluations import Evaluation
from app.models.tasks import Task, TaskStatuses
from app.models.teams import Team, UserRoles, UserTeam
from app.models.users import User
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


@pytest.fixture
def team_data():
    return TeamCreateSchema(name='team_name1')


@pytest.mark.asyncio
class TestTeamManager:
    async def test_create_team(self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]):
        manager = TeamManager(session)

        new_team_1 = await manager.create_team(team_data, users[0])
        new_team_2 = await manager.create_team(team_data, users[1])

        assert isinstance(new_team_1, Team)
        assert isinstance(new_team_2, Team)
        assert new_team_1.name == team_data.name
        assert new_team_2.name == team_data.name

        stmt = select(UserTeam).where(UserTeam.user_id == users[0].id, UserTeam.team_id == new_team_1.id)
        result = await session.execute(stmt)
        user_team_association = result.scalar_one()
        assert user_team_association.role == UserRoles.ADMIN

        stmt = select(UserTeam).where(UserTeam.user_id == users[1].id, UserTeam.team_id == new_team_2.id)
        result = await session.execute(stmt)
        user_team_association = result.scalar_one()
        assert user_team_association.role == UserRoles.ADMIN

    async def test_assign_role(self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]):
        manager = TeamManager(session)
        new_team = await manager.create_team(team_data, users[0])

        new_manager_association = await manager.assign_role(users[1].id, new_team.id, UserRoles.MANAGER)
        new_member_association = await manager.assign_role(users[2].id, new_team.id, UserRoles.USER)

        assert isinstance(new_manager_association, UserTeam)
        assert isinstance(new_member_association, UserTeam)
        assert new_manager_association.user_id == users[1].id
        assert new_manager_association.team_id == new_team.id
        assert new_manager_association.role == UserRoles.MANAGER
        assert new_member_association.role == UserRoles.USER

        stmt = select(func.count()).select_from(UserTeam).where(UserTeam.team_id == new_team.id)
        result = await session.execute(stmt)
        user_in_team_count = result.scalar_one()
        assert user_in_team_count == 3

    async def test_get_users(self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]):
        manager = TeamManager(session)
        new_team = await manager.create_team(team_data, users[0])
        await manager.assign_role(users[1].id, new_team.id, UserRoles.MANAGER)
        await manager.assign_role(users[2].id, new_team.id, UserRoles.USER)

        team_users = await manager.get_users(new_team.id)

        assert len(team_users) == 3
        assert isinstance(team_users[0], tuple)
        assert isinstance(team_users[0][0], User)
        assert isinstance(team_users[0][1], UserRoles)

    async def test_get_teams_by_user(self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]):
        manager = TeamManager(session)
        await manager.create_team(team_data, users[0])
        await manager.create_team(team_data, users[0])
        await manager.create_team(team_data, users[0])

        user_teams = await manager.get_teams_by_user(users[0].id)

        assert len(user_teams) == 3
        assert isinstance(user_teams[0], tuple)
        assert isinstance(user_teams[0][0], Team)
        assert isinstance(user_teams[0][1], UserRoles)

    async def test_delete_user_team_association(
        self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]
    ):
        manager = TeamManager(session)
        new_team = await manager.create_team(team_data, users[0])
        await manager.assign_role(users[1].id, new_team.id, UserRoles.MANAGER)
        await manager.assign_role(users[2].id, new_team.id, UserRoles.USER)

        await manager.delete_user_team_association(users[1].id, new_team.id)

        stmt = select(func.count()).select_from(UserTeam).where(UserTeam.team_id == new_team.id)
        result = await session.execute(stmt)
        user_in_team_count = result.scalar_one()
        assert user_in_team_count == 2

        await manager.delete_user_team_association(users[0].id, new_team.id)
        await manager.delete_user_team_association(users[2].id, new_team.id)

        stmt = select(func.count()).select_from(UserTeam).where(UserTeam.team_id == new_team.id)
        result = await session.execute(stmt)
        user_in_team_count = result.scalar_one()
        assert user_in_team_count == 0

        stmt = select(Team).where(Team.id == new_team.id)
        result = await session.execute(stmt)
        deleted_team = result.scalar_one_or_none()
        assert deleted_team is None

    async def test_get_avg_evaluation(self, session: AsyncSession, team_data: TeamCreateSchema, users: list[User]):
        manager = TeamManager(session)
        new_team = await manager.create_team(team_data, users[0])

        evaluations = []
        for i in range(1, 5):
            evaluation = i % 5 + 1
            evaluations.append(evaluation)
            new_task = Task(
                description=f'description{i}',
                deadline=date.today() - timedelta(days=i % 3),
                status=TaskStatuses.COMPLETED,
                performer_id=users[0].id,
                team_id=new_team.id,
            )
            session.add(new_task)
            await session.flush()

            new_evaluation = Evaluation(
                value=evaluation,
                evaluator_id=users[1].id,
                task_id=new_task.id,
            )
            session.add(new_evaluation)

        avg_evaluation = await manager.get_avg_evaluation(users[0].id, new_team.id)
        assert avg_evaluation == round(sum(evaluations) / len(evaluations), 2)
