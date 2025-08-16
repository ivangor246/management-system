from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user, require_manager, require_user
from app.models.users import User
from app.schemas.tasks import TaskCreateSchema, TaskCreateSuccessSchema, TaskSchema
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


@tasks_router.get('/teams/{team_id:int}')
async def get_tasks_by_team(
    service: Annotated[TaskService, Depends(get_task_service)],
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[TaskSchema]:
    return await service.get_tasks_by_team(team_id)


@tasks_router.get('/my')
async def get_tasks_by_performer(
    service: Annotated[TaskService, Depends(get_task_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
) -> list[TaskSchema]:
    return await service.get_tasks_by_performer(auth_user.id)
