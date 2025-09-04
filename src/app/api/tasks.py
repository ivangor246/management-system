from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_manager, require_member
from app.models.users import User
from app.schemas.evaluations import EvaluationSchema, EvaluationSuccessSchema
from app.schemas.tasks import (
    TaskCreateSchema,
    TaskCreateSuccessSchema,
    TaskSchema,
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
    """
    Create a new task for a specified team.

    Args:
        service (TaskService): Task service dependency.
        task_data (TaskCreateSchema): Data for the new task.
        team_id (int): ID of the team where the task will be created.
        manager (User): Team manager creating the task.

    Returns:
        TaskCreateSuccessSchema: ID of the newly created task.
    """
    return await service.create_task(task_data, team_id)


@tasks_router.get('/')
async def get_tasks_by_team(
    service: Annotated[TaskService, Depends(get_task_service)],
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> list[TaskSchema]:
    """
    Retrieve all tasks for a team.

    Args:
        service (TaskService): Task service dependency.
        team_id (int): ID of the team.
        member (User): User requesting tasks.

    Returns:
        list[TaskSchema]: List of tasks for the team.
    """
    return await service.get_tasks_by_team(team_id)


@tasks_router.get('/mine')
async def get_my_tasks_in_team(
    service: Annotated[TaskService, Depends(get_task_service)],
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> list[TaskSchema]:
    """
    Retrieve tasks assigned to the current user within a team.

    Args:
        service (TaskService): Task service dependency.
        team_id (int): ID of the team.
        member (User): Current user.

    Returns:
        list[TaskSchema]: List of tasks assigned to the user.
    """
    return await service.get_tasks_by_performer(member.id, team_id)


@tasks_router.put('/{task_id:int}')
async def update_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_data: TaskUpdateSchema,
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> TaskUpdateSuccessSchema:
    """
    Update a task's details.

    Args:
        service (TaskService): Task service dependency.
        task_data (TaskUpdateSchema): Updated task data.
        task_id (int): ID of the task to update.
        team_id (int): ID of the team.
        member (User): User updating the task.

    Returns:
        TaskUpdateSuccessSchema: Success response for the update.
    """
    return await service.update_task(task_id, task_data)


@tasks_router.post('/{task_id:int}/evaluation')
async def update_task_evaluation(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_id: int,
    evaluation_data: EvaluationSchema,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> EvaluationSuccessSchema:
    """
    Update or create the evaluation of a task.

    Args:
        service (TaskService): Task service dependency.
        task_id (int): ID of the task to update.
        evaluation_data (EvaluationSchema): New evaluation data.
        team_id (int): ID of the team.
        manager (User): Team manager performing the update.

    Returns:
        EvaluationSuccessSchema: Success response for the evaluation update.
    """
    return await service.update_task_evaluation(task_id, manager.id, evaluation_data)


@tasks_router.delete('/{task_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    service: Annotated[TaskService, Depends(get_task_service)],
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_member)],
):
    """
    Delete a task from a team.

    Args:
        service (TaskService): Task service dependency.
        task_id (int): ID of the task to delete.
        team_id (int): ID of the team.
        member (User): User performing the deletion.

    Returns:
        None
    """
    await service.delete_task(task_id)


tasks_router.include_router(comments_router)
