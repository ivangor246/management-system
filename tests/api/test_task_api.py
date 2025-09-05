from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import TokenMixin
from app.main import create_app
from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.users import User
from app.schemas.evaluations import EvaluationSchema
from app.schemas.tasks import TaskCreateSchema, TaskStatuses, TaskUpdateSchema
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
class TestTasksAPI:
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

    async def test_create_task(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)

        task_data = TaskCreateSchema(
            description='Test Task',
            deadline=date.today() + timedelta(days=7),
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                f'/api/teams/{team.id}/tasks/',
                json=task_data.model_dump(mode='json'),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'task_id' in response.json()

    async def test_get_tasks_by_team(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        task_manager = TaskManager(session)
        await task_manager.create_task(TaskCreateSchema(description='Task 1', deadline=date.today()), team.id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/tasks/',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]['description'] == 'Task 1'

    async def test_get_my_tasks_in_team(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        task_manager = TaskManager(session)
        await task_manager.create_task(
            TaskCreateSchema(description='Task 2', deadline=date.today(), performer_id=manager_user.id), team.id
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get(
                f'/api/teams/{team.id}/tasks/mine',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['performer_id'] == manager_user.id

    async def test_update_task(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        task_manager = TaskManager(session)
        task = await task_manager.create_task(TaskCreateSchema(description='Task 3', deadline=date.today()), team.id)

        task_update = TaskUpdateSchema(description='Updated Task 3', status=TaskStatuses.WORK)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.put(
                f'/api/teams/{team.id}/tasks/{task.id}',
                json=task_update.model_dump(exclude_unset=True),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['detail'] == 'The task has been successfully updated'

    async def test_delete_task(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        task_manager = TaskManager(session)
        task = await task_manager.create_task(TaskCreateSchema(description='Task 5', deadline=date.today()), team.id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.delete(
                f'/api/teams/{team.id}/tasks/{task.id}',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_update_task_evaluation(self, app: FastAPI, session: AsyncSession, user_data):
        manager_user, token = await self._create_user_and_token(session, user_data)
        team = await self._create_team_with_manager(session, manager_user)
        task_manager = TaskManager(session)
        task = await task_manager.create_task(TaskCreateSchema(description='Task 4', deadline=date.today()), team.id)

        score_data = EvaluationSchema(value=5)

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.post(
                f'/api/teams/{team.id}/tasks/{task.id}/evaluation',
                json=score_data.model_dump(),
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['detail'] == 'The task evaluation has been successfully updated'
