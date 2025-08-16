from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.tasks import Task
from app.schemas.tasks import TaskCreateSchema


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


def get_task_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskManager:
    return TaskManager(session=session)
