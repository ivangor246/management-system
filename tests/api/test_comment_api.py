from datetime import date

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import TokenMixin
from app.main import create_app
from app.managers.comments import CommentManager
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.comments import CommentCreateSchema
from app.schemas.tasks import TaskCreateSchema, TaskStatuses
from app.schemas.teams import TeamCreateSchema
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
class TestCommentsAPI:
    async def _create_user_and_token(self, session: AsyncSession, user_data) -> tuple[User, str]:
        user_manager = UserManager(session)
        user = await user_manager.create_user(user_data)
        token = TokenMixin().generate_access_token(user.email)
        return user, token

    async def _create_team(self, session: AsyncSession, user: User):
        team_manager = TeamManager(session)
        team = await team_manager.create_team(TeamCreateSchema(name='Test Team'), user)
        return team

    async def _create_task(self, session: AsyncSession, team_id: int, user: User, description='Task for comments'):
        task_manager = TaskManager(session)
        task = await task_manager.create_task(
            TaskCreateSchema(
                description=description,
                deadline=date.today(),
                status=TaskStatuses.OPEN,
                performer_id=user.id,
            ),
            team_id,
        )
        return task

    async def test_create_comment(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team(session, user)
        task = await self._create_task(session, team.id, user)

        comment_data = CommentCreateSchema(text='Test comment')

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                f'/api/teams/{team.id}/tasks/{task.id}/comments/',
                json=comment_data.model_dump(),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'comment_id' in response.json()

    async def test_get_comments_by_task(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team(session, user)
        task = await self._create_task(session, team.id, user)
        comment_manager = CommentManager(session)
        await comment_manager.create_comment(CommentCreateSchema(text='First comment'), user.id, task.id, team.id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/tasks/{task.id}/comments/',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]['text'] == 'First comment'
        assert data[0]['user_id'] == user.id

    async def test_delete_comment(self, app: FastAPI, session: AsyncSession, user_data):
        user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team(session, user)
        task = await self._create_task(session, team.id, user)
        comment_manager = CommentManager(session)
        comment = await comment_manager.create_comment(CommentCreateSchema(text='Delete me'), user.id, task.id, team.id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.delete(
                f'/api/teams/{team.id}/tasks/{task.id}/comments/{comment.id}',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT
