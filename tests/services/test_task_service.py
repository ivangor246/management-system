from datetime import date

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.tasks import Task, TaskStatuses
from app.models.teams import Team
from app.models.users import User
from app.schemas.evaluations import EvaluationSchema
from app.schemas.tasks import (
    TaskCreateSchema,
    TaskUpdateSchema,
)
from app.schemas.teams import TeamCreateSchema
from app.schemas.users import UserCreateSchema
from app.services.tasks import TaskService


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
async def user(session: AsyncSession, user_data: UserCreateSchema) -> User:
    manager = UserManager(session)
    return await manager.create_user(user_data)


@pytest.fixture
def team_data():
    return TeamCreateSchema(name='Team1')


@pytest_asyncio.fixture
async def team(session: AsyncSession, user: User, team_data: TeamCreateSchema) -> Team:
    manager = TeamManager(session)
    return await manager.create_team(team_data, user)


@pytest.mark.asyncio
class TestTaskService:
    async def test_create_task(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task_data = TaskCreateSchema(
            description='Test Task',
            deadline=date.today(),
            status=TaskStatuses.OPEN,
            performer_id=user.id,
        )

        response = await service.create_task(task_data, team.id)
        assert response.task_id is not None
        assert response.detail == 'The task has been successfully created'

        task = await session.get(Task, response.task_id)
        assert task.description == task_data.description
        assert task.team_id == team.id

    async def test_get_tasks_by_team(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task = Task(
            description='Team task',
            deadline=date.today(),
            performer_id=user.id,
            team_id=team.id,
        )
        session.add(task)
        await session.commit()

        tasks = await service.get_tasks_by_team(team.id)
        assert len(tasks) == 1
        assert tasks[0].description == 'Team task'

    async def test_get_tasks_by_performer(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task = Task(
            description='Performer task',
            deadline=date.today(),
            performer_id=user.id,
            team_id=team.id,
        )
        session.add(task)
        await session.commit()

        tasks = await service.get_tasks_by_performer(user.id, team.id)
        assert len(tasks) == 1
        assert tasks[0].performer_id == user.id

    async def test_update_task(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task = Task(
            description='Old desc',
            deadline=date.today(),
            performer_id=user.id,
            team_id=team.id,
        )
        session.add(task)
        await session.commit()

        update_data = TaskUpdateSchema(description='New desc')
        response = await service.update_task(task.id, update_data)

        assert response.detail == 'The task has been successfully updated'

        updated_task = await session.get(Task, task.id)
        assert updated_task.description == 'New desc'

    async def test_update_task_not_found(self, session: AsyncSession):
        manager = TaskManager(session)
        service = TaskService(manager)

        update_data = TaskUpdateSchema(description='New desc')

        with pytest.raises(HTTPException) as exc_info:
            await service.update_task(999, update_data)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_task(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task = Task(
            description='To delete',
            deadline=date.today(),
            performer_id=user.id,
            team_id=team.id,
        )
        session.add(task)
        await session.commit()

        await service.delete_task(task.id)

        deleted_task = await session.get(Task, task.id)
        assert deleted_task is None

    async def test_delete_task_not_found(self, session: AsyncSession):
        manager = TaskManager(session)
        service = TaskService(manager)

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_task(999)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_task_evaluation(self, session: AsyncSession, team: Team, user: User):
        manager = TaskManager(session)
        service = TaskService(manager)

        task = Task(
            description='Task with score',
            deadline=date.today(),
            performer_id=user.id,
            team_id=team.id,
        )
        session.add(task)
        await session.commit()

        evaluation_data = EvaluationSchema(value=4)
        response = await service.update_task_evaluation(task.id, user.id, evaluation_data)
        assert response.detail == 'The task evaluation has been successfully updated'

        updated_task = await session.scalar(
            select(Task).options(selectinload(Task.evaluation)).where(Task.id == task.id)
        )
        assert updated_task.evaluation.value == 4

    async def test_update_task_evaluation_not_found(self, session: AsyncSession):
        manager = TaskManager(session)
        service = TaskService(manager)

        evaluation_data = EvaluationSchema(value=3)
        with pytest.raises(HTTPException) as exc_info:
            await service.update_task_evaluation(999, 1, evaluation_data)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
