from datetime import date, timedelta

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.tasks import TaskManager
from app.managers.teams import TeamManager
from app.managers.users import UserManager
from app.models.tasks import Task, TaskStatuses
from app.models.teams import Team, UserRoles
from app.models.users import User
from app.schemas.evaluations import EvaluationSchema
from app.schemas.tasks import TaskCreateSchema, TaskUpdateSchema
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
def task_data() -> TaskCreateSchema:
    return TaskCreateSchema(
        description='description1',
        deadline=date.today() + timedelta(days=5),
        status=TaskStatuses.OPEN,
        performer_id=1,
    )


@pytest.mark.asyncio
class TestTaskManager:
    async def test_create_task(self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team):
        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        task_data_2 = task_data.model_copy()
        task_data_2.performer_id = users[2].id
        task_data_2.status = TaskStatuses.WORK

        new_task_1 = await manager.create_task(task_data, team.id)
        new_task_2 = await manager.create_task(task_data_2, team.id)

        assert isinstance(new_task_1, Task)
        assert isinstance(new_task_2, Task)
        assert new_task_1.description == task_data.description
        assert new_task_1.deadline == task_data.deadline
        assert new_task_1.status == task_data.status
        assert new_task_1.performer_id == task_data.performer_id
        assert new_task_2.performer_id == task_data_2.performer_id

        stmt = select(func.count()).select_from(Task).where(Task.team_id == team.id)
        result = await session.execute(stmt)
        task_in_team_count = result.scalar_one()
        assert task_in_team_count == 2

    async def test_get_tasks_by_team(
        self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team
    ):
        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        task_data_2 = task_data.model_copy()
        task_data_2.performer_id = users[2].id
        task_data_2.status = TaskStatuses.WORK
        await manager.create_task(task_data, team.id)
        await manager.create_task(task_data_2, team.id)

        tasks = await manager.get_tasks_by_team(team.id)

        assert len(tasks) == 2
        assert isinstance(tasks[0], Task)
        assert tasks[0].team_id == team.id
        assert tasks[1].team_id == team.id

    async def test_get_tasks_by_performer(
        self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team
    ):
        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        task_data_2 = task_data.model_copy()
        task_data_2.performer_id = users[2].id
        await manager.create_task(task_data, team.id)
        await manager.create_task(task_data, team.id)
        await manager.create_task(task_data_2, team.id)

        tasks = await manager.get_tasks_by_performer(users[1].id, team.id)

        assert len(tasks) == 2
        assert isinstance(tasks[0], Task)
        assert tasks[0].team_id == team.id
        assert tasks[0].performer_id == users[1].id
        assert tasks[1].performer_id == users[1].id

    async def test_update_task(self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team):
        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        new_task = await manager.create_task(task_data, team.id)

        task_data_for_update = TaskUpdateSchema(
            description='description2',
            deadline=date.today() + timedelta(days=3),
        )
        updated_task = await manager.update_task(task_data_for_update, new_task.id, team.id)
        assert updated_task.description == task_data_for_update.description
        assert updated_task.deadline == task_data_for_update.deadline

        task_data_for_update = TaskUpdateSchema(
            status=TaskStatuses.WORK,
            performer_id=users[2].id,
        )
        updated_task = await manager.update_task(task_data_for_update, new_task.id, team.id)
        assert updated_task.status == task_data_for_update.status
        assert updated_task.performer_id == task_data_for_update.performer_id

    async def test_delete_task(self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team):
        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        task_data_2 = task_data.model_copy()
        task_data_2.performer_id = users[2].id
        new_task_1 = await manager.create_task(task_data, team.id)
        new_task_2 = await manager.create_task(task_data_2, team.id)

        await manager.delete_task(new_task_1.id, team.id)
        tasks = await manager.get_tasks_by_team(team.id)
        assert len(tasks) == 1

        await manager.delete_task(new_task_2.id, team.id)
        tasks = await manager.get_tasks_by_team(team.id)
        assert len(tasks) == 0

    async def test_update_task_evaluation(
        self, session: AsyncSession, task_data: TaskCreateSchema, users: list[User], team: Team
    ):
        with pytest.raises(ValidationError):
            EvaluationSchema(value=6)
        with pytest.raises(ValidationError):
            EvaluationSchema(value=0)

        manager = TaskManager(session)
        task_data.performer_id = users[1].id
        task_data_2 = task_data.model_copy()
        task_data_2.performer_id = users[2].id
        new_task_1 = await manager.create_task(task_data, team.id)
        new_task_2 = await manager.create_task(task_data_2, team.id)

        evaluation_data_1 = EvaluationSchema(value=1)
        evaluation_data_2 = EvaluationSchema(value=5)

        new_evaluation_1 = await manager.update_task_evaluation(new_task_1.id, team.id, users[0].id, evaluation_data_1)
        new_evaluation_2 = await manager.update_task_evaluation(new_task_2.id, team.id, users[0].id, evaluation_data_2)

        assert new_evaluation_1.value == evaluation_data_1.value
        assert new_evaluation_2.value == evaluation_data_2.value
        assert new_evaluation_1.evaluator_id == users[0].id
        assert new_evaluation_1.task_id == new_task_1.id

        evaluation_data_3 = EvaluationSchema(value=3)
        new_evaluation_3 = await manager.update_task_evaluation(new_task_1.id, team.id, users[2].id, evaluation_data_3)

        assert new_evaluation_3.value == evaluation_data_3.value
        assert new_evaluation_3.evaluator_id == users[2].id
