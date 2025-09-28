from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.comments import CommentManager
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.comments import Comment
from app.models.tasks import Task, TaskStatuses
from app.models.teams import Team, UserRoles
from app.models.users import User
from app.schemas.comments import CommentCreateSchema
from app.schemas.tasks import TaskCreateSchema
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


@pytest_asyncio.fixture
async def task(session: AsyncSession, users: list[User], team: Team) -> Task:
    task_manager = TaskManager(session)
    task_data = TaskCreateSchema(
        description='description1',
        deadline=date.today(),
        status=TaskStatuses.OPEN,
        performer_id=users[1].id,
    )
    new_task = await task_manager.create_task(task_data, team.id)
    return new_task


@pytest.fixture
def comment_data() -> CommentCreateSchema:
    return CommentCreateSchema(text='comment1')


@pytest.mark.asyncio
class TestCommentManager:
    async def test_create_comment(
        self,
        session: AsyncSession,
        comment_data: CommentCreateSchema,
        task: Task,
        users: list[User],
        team: Team,
    ):
        manager = CommentManager(session)

        new_comment_1 = await manager.create_comment(comment_data, users[1].id, task.id, team.id)
        new_comment_2 = await manager.create_comment(comment_data, users[2].id, task.id, team.id)

        assert isinstance(new_comment_1, Comment)
        assert isinstance(new_comment_2, Comment)
        assert new_comment_1.task_id == task.id
        assert new_comment_2.task_id == task.id
        assert new_comment_1.user_id == users[1].id
        assert new_comment_2.user_id == users[2].id

        stmt = select(func.count()).select_from(Comment).where(Comment.task_id == task.id)
        result = await session.execute(stmt)
        comment_in_task_count = result.scalar_one()
        assert comment_in_task_count == 2

    async def test_get_comments_by_task(
        self,
        session: AsyncSession,
        comment_data: CommentCreateSchema,
        task: Task,
        users: list[User],
        team: Team,
    ):
        manager = CommentManager(session)
        await manager.create_comment(comment_data, users[1].id, task.id, team.id)
        await manager.create_comment(comment_data, users[1].id, task.id, team.id)
        await manager.create_comment(comment_data, users[2].id, task.id, team.id)

        task_comments = await manager.get_comments_by_task(task.id, team.id)

        assert len(task_comments) == 3
        assert isinstance(task_comments[0], Comment)
        assert task_comments[0].task_id == task.id
        assert task_comments[1].task_id == task.id
        assert task_comments[2].task_id == task.id

    async def test_delete_comment(
        self,
        session: AsyncSession,
        comment_data: CommentCreateSchema,
        task: Task,
        users: list[User],
        team: Team,
    ):
        manager = CommentManager(session)
        new_comment_1 = await manager.create_comment(comment_data, users[1].id, task.id, team.id)
        new_comment_2 = await manager.create_comment(comment_data, users[2].id, task.id, team.id)

        await manager.delete_comment(new_comment_1.id, task.id, team.id)
        comments = await manager.get_comments_by_task(task.id, team.id)
        assert len(comments) == 1

        await manager.delete_comment(new_comment_2.id, task.id, team.id)
        comments = await manager.get_comments_by_task(task.id, team.id)
        assert len(comments) == 0
