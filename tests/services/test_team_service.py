from datetime import date, timedelta

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.evaluations import Evaluation
from app.models.tasks import Task
from app.models.teams import Team, UserTeam
from app.models.users import User
from app.schemas.teams import (
    TeamByMemberSchema,
    TeamCreateSchema,
    TeamCreateSuccessSchema,
    TeamMemberSchema,
    UserRoles,
    UserTeamCreateSchema,
    UserTeamCreateSuccessSchema,
)
from app.schemas.users import UserCreateSchema
from app.services.teams import TeamService


@pytest.fixture
def team_data():
    return TeamCreateSchema(name='team1')


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


@pytest.mark.asyncio
class TestTeamService:
    async def test_create_team(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)

        response = await service.create_team(team_data, user)

        assert isinstance(response, TeamCreateSuccessSchema)

        stmt = select(Team).where(Team.id == response.team_id)
        result = await session.execute(stmt)
        created_team = result.scalar_one()
        assert created_team.name == team_data.name

        stmt = select(UserTeam).where(UserTeam.user_id == user.id, UserTeam.team_id == created_team.id)
        result = await session.execute(stmt)
        assoc = result.scalar_one()
        assert assoc.role == UserRoles.ADMIN

    async def test_get_users(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)

        team = await manager.create_team(team_data, user)
        users = await service.get_users(team.id)

        assert len(users) == 1
        assert isinstance(users[0], TeamMemberSchema)
        assert users[0].user_id == user.id
        assert users[0].username == user.username
        assert users[0].role == UserRoles.ADMIN

    async def test_get_users_team_not_found(self, session: AsyncSession):
        manager = TeamManager(session)
        service = TeamService(manager)

        with pytest.raises(HTTPException) as exc_info:
            await service.get_users(team_id=999)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_teams_by_user(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)

        team = await manager.create_team(team_data, user)
        teams = await service.get_teams_by_user(user.id)

        assert len(teams) == 1
        assert isinstance(teams[0], TeamByMemberSchema)
        assert teams[0].team_id == team.id
        assert teams[0].name == team.name
        assert teams[0].role == UserRoles.ADMIN

    async def test_create_user_team_association(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)
        new_user_data = UserCreateSchema(
            username='username2',
            email='email2@email.com',
            password='password2',
            first_name='first_name2',
            last_name='last_name2',
        )

        team = await manager.create_team(team_data, user)
        user2 = await UserManager(session).create_user(new_user_data)

        user_team_data = UserTeamCreateSchema(user_id=user2.id, role=UserRoles.MANAGER)
        response = await service.create_user_team_association(user_team_data, team.id)

        assert isinstance(response, UserTeamCreateSuccessSchema)

        stmt = select(UserTeam).where(UserTeam.user_id == user2.id, UserTeam.team_id == team.id)
        result = await session.execute(stmt)
        assoc = result.scalar_one()
        assert assoc.role == UserRoles.MANAGER

    async def test_remove_user_from_team(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)

        team = await manager.create_team(team_data, user)

        await service.remove_user_from_team(user.id, team.id)

        stmt = select(UserTeam).where(UserTeam.user_id == user.id, UserTeam.team_id == team.id)
        result = await session.execute(stmt)
        assoc = result.scalar_one_or_none()
        assert assoc is None

    async def test_remove_user_from_team_not_found(self, session: AsyncSession):
        manager = TeamManager(session)
        service = TeamService(manager)

        with pytest.raises(HTTPException) as exc_info:
            await service.remove_user_from_team(user_id=1, team_id=999)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_avg_evaluation(self, session: AsyncSession, user: User, team_data: TeamCreateSchema):
        manager = TeamManager(session)
        service = TeamService(manager)

        team = await manager.create_team(team_data, user)

        today = date.today()
        task_1 = Task(
            description='description1',
            performer_id=user.id,
            team_id=team.id,
            deadline=today,
        )
        task_2 = Task(
            description='description2',
            performer_id=user.id,
            team_id=team.id,
            deadline=today + timedelta(days=1),
        )
        session.add_all([task_1, task_2])
        await session.flush()

        evaluation_1 = Evaluation(
            value=4,
            evaluator_id=user.id,
            task_id=task_1.id,
        )
        evaluation_2 = Evaluation(
            value=2,
            evaluator_id=user.id,
            task_id=task_2.id,
        )
        session.add_all([evaluation_1, evaluation_2])
        await session.commit()

        avg = await service.get_avg_evaluation(user.id, team.id)
        assert avg == 3.0
