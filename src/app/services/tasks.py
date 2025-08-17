from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.tasks import TaskManager, get_task_manager
from app.schemas.tasks import (
    TaskCreateSchema,
    TaskCreateSuccessSchema,
    TaskSchema,
    TaskUpdateSchema,
    TaskUpdateSuccessSchema,
)


class TaskService:
    def __init__(self, manager: TaskManager):
        self.manager = manager

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> TaskCreateSuccessSchema:
        try:
            new_task = await self.manager.create_task(task_data, team_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when creating the task',
            )
        return TaskCreateSuccessSchema(task_id=new_task.id)

    async def get_tasks_by_team(self, team_id: int) -> list[TaskSchema]:
        tasks = await self.manager.get_tasks_by_team(team_id)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def get_tasks_by_performer(self, performer_id: int, team_id: int) -> list[TaskSchema]:
        tasks = await self.manager.get_tasks_by_performer(performer_id, team_id)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def update_task(self, task_id: int, task_data: TaskUpdateSchema) -> TaskUpdateSuccessSchema:
        try:
            task = await self.manager.update_task(task_id, task_data)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='The task was not found',
                )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when updating the task',
            )

        return TaskUpdateSuccessSchema()

    async def delete_task(self, task_id: int) -> None:
        deleted = await self.manager.delete_task(task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The task was not found',
            )


def get_task_service(manager: Annotated[TaskManager, Depends(get_task_manager)]) -> TaskService:
    return TaskService(manager=manager)
