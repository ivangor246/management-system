from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.comments import CommentManager
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.comments import Comment
from app.models.tasks import Task
from app.models.teams import Team
from app.models.users import User
from app.schemas.comments import CommentCreateSchema
from app.schemas.tasks import TaskCreateSchema
from app.schemas.teams import TeamCreateSchema
from app.schemas.users import UserCreateSchema
from app.services.comments import CommentService


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


@pytest.fixture
def team_data():
    return TeamCreateSchema(name='team_name1')


@pytest_asyncio.fixture
async def team(session: AsyncSession, user: User, team_data) -> Team:
    manager = TeamManager(session)
    return await manager.create_team(team_data, user)


@pytest_asyncio.fixture
async def task(session: AsyncSession, user: User, team: Team) -> Task:
    today = date.today()
    task_data = TaskCreateSchema(
        description='task_description1',
        deadline=today + timedelta(days=5),
        performer_id=user.id,
        team_id=team.id,
    )
    manager = TaskManager(session)
    return await manager.create_task(task_data, team.id)


@pytest.mark.asyncio
class TestCommentService:
    async def test_create_comment(self, session: AsyncSession, user: User, task: Task, team: Team):
        service = CommentService(CommentManager(session))
        comment_data = CommentCreateSchema(text='comment1')

        result = await service.create_comment(comment_data, user.id, task.id, team.id)
        assert result.comment_id is not None
        assert result.detail == 'Comment has been successfully created'

        stmt = await session.execute(Comment.__table__.select().where(Comment.id == result.comment_id))
        comment = stmt.fetchone()
        assert comment is not None

    async def test_get_comments_by_task(self, session: AsyncSession, user: User, task: Task, team: Team):
        service = CommentService(CommentManager(session))
        comment_data = CommentCreateSchema(text='comment2')

        await service.create_comment(comment_data, user.id, task.id, team.id)
        comments = await service.get_comments_by_task(task.id, team.id)
        assert len(comments) == 1
        assert comments[0].text == comment_data.text
        assert comments[0].user_id == user.id
        assert comments[0].task_id == task.id

    async def test_delete_comment(self, session: AsyncSession, user: User, task: Task, team: Team):
        service = CommentService(CommentManager(session))
        comment_data = CommentCreateSchema(text='comment_to_delete')

        created = await service.create_comment(comment_data, user.id, task.id, team.id)
        await service.delete_comment(created.comment_id, task.id, team.id)

        stmt = await session.execute(Comment.__table__.select().where(Comment.id == created.comment_id))
        comment = stmt.fetchone()
        assert comment is None
