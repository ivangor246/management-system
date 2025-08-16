from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_manager
from app.models.users import User
from app.schemas.tasks import TaskCreateSchema, TaskCreateSuccessSchema
from app.services.tasks import TaskService, get_task_service

tasks_router = APIRouter(prefix='/tasks', tags=['tasks'])


@tasks_router.post('/teams/{team_id:int}', status_code=status.HTTP_201_CREATED)
async def create_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_data: TaskCreateSchema,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> TaskCreateSuccessSchema:
    return await service.create_task(task_data, team_id)
