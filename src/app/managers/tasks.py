from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.tasks import Task
from app.schemas.tasks import TaskCreateSchema, TaskUpdateSchema


class TaskManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> Task:
        new_task = Task(
            description=task_data.description,
            deadline=task_data.deadline,
            status=task_data.status,
            performer_id=task_data.performer_id,
            team_id=team_id,
        )
        self.session.add(new_task)

        try:
            await self.session.commit()
            await self.session.refresh(new_task)
        except:
            await self.session.rollback()
            raise

        return new_task

    async def get_tasks_by_team(self, team_id: int) -> list[Task]:
        stmt = select(Task).where(Task.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalars()

    async def get_tasks_by_performer(self, performer_id: int) -> list[Task]:
        stmt = select(Task).where(Task.performer_id == performer_id)
        result = await self.session.execute(stmt)
        return result.scalars()

    async def update_task(self, task_id: int, task_data: TaskUpdateSchema) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return None

        if task_data.description is not None:
            task.description = task_data.description
        if task_data.deadline is not None:
            task.deadline = task_data.deadline
        if task_data.status is not None:
            task.status = task_data.status
        if task_data.performer_id is not None:
            task.performer_id = task_data.performer_id

        try:
            await self.session.commit()
            await self.session.refresh(task)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return task

    async def delete_task(self, task_id: int) -> bool:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return False

        await self.session.delete(task)
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True


def get_task_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskManager:
    return TaskManager(session=session)
