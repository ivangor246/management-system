from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user, require_manager, require_user
from app.models.users import User
from app.schemas.tasks import (
    TaskCreateSchema,
    TaskCreateSuccessSchema,
    TaskSchema,
    TaskScoreSchema,
    TaskScoreSuccessSchema,
    TaskUpdateSchema,
    TaskUpdateSuccessSchema,
)
from app.services.tasks import TaskService, get_task_service

from .comments import comments_router

tasks_router = APIRouter(prefix='/{team_id:int}/tasks', tags=['tasks'])


@tasks_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_data: TaskCreateSchema,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> TaskCreateSuccessSchema:
    return await service.create_task(task_data, team_id)


@tasks_router.get('/')
async def get_tasks_by_team(
    service: Annotated[TaskService, Depends(get_task_service)],
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[TaskSchema]:
    return await service.get_tasks_by_team(team_id)


@tasks_router.get('/mine')
async def get_my_tasks_in_team(
    service: Annotated[TaskService, Depends(get_task_service)],
    team_id: int,
    auth_user: Annotated[User, Depends(get_request_user)],
) -> list[TaskSchema]:
    return await service.get_tasks_by_performer(auth_user.id, team_id)


@tasks_router.put('/{task_id:int}')
async def update_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_data: TaskUpdateSchema,
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> TaskUpdateSuccessSchema:
    return await service.update_task(task_id, task_data)


@tasks_router.put('/{task_id:int}/score')
async def update_task_score(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_score: TaskScoreSchema,
    task_id: int,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> TaskScoreSuccessSchema:
    return await service.update_task_score(task_id, task_score)


@tasks_router.delete('/{task_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
):
    await service.delete_task(task_id)


tasks_router.include_router(comments_router)
