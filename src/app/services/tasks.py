from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.tasks import TaskManager, get_task_manager
from app.schemas.evaluations import EvaluationSchema, EvaluationSuccessSchema
from app.schemas.tasks import (
    TaskCreateSchema,
    TaskCreateSuccessSchema,
    TaskSchema,
    TaskUpdateSchema,
    TaskUpdateSuccessSchema,
)


class TaskService:
    """
    Service responsible for handling tasks within a team.

    Attributes:
        manager (TaskManager): Manager responsible for task database operations.

    Methods:
        create_task(task_data: TaskCreateSchema, team_id: int) -> TaskCreateSuccessSchema:
            Creates a new task for the specified team.
        get_tasks_by_team(team_id: int) -> list[TaskSchema]:
            Retrieves all tasks for a given team.
        get_tasks_by_performer(performer_id: int, team_id: int) -> list[TaskSchema]:
            Retrieves tasks assigned to a specific performer within a team.
        update_task(task_id: int, task_data: TaskUpdateSchema) -> TaskUpdateSuccessSchema:
            Updates an existing task.
        delete_task(task_id: int) -> None:
            Deletes a task by its ID.
        update_task_score(task_id: int, task_score: EvaluationSchema) -> EvaluationSuccessSchema:
            Updates the score of a specific task.
    """

    def __init__(self, manager: TaskManager):
        """
        Initializes the TaskService with a TaskManager.

        Args:
            manager (TaskManager): The manager instance for handling task operations.
        """
        self.manager = manager

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> TaskCreateSuccessSchema:
        """
        Creates a new task for the specified team.

        Args:
            task_data (TaskCreateSchema): Data required to create the task.
            team_id (int): ID of the team the task belongs to.

        Returns:
            TaskCreateSuccessSchema: Schema containing the ID of the newly created task.

        Raises:
            HTTPException: If an error occurs during task creation.
        """
        try:
            new_task = await self.manager.create_task(task_data, team_id)
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when creating the task',
            )
        return TaskCreateSuccessSchema(task_id=new_task.id)

    async def get_tasks_by_team(self, team_id: int) -> list[TaskSchema]:
        """
        Retrieves all tasks for a given team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[TaskSchema]: List of TaskSchema objects. Each task includes its evaluation value
            if it exists.
        """
        tasks = await self.manager.get_tasks_by_team(team_id)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def get_tasks_by_performer(self, performer_id: int, team_id: int) -> list[TaskSchema]:
        """
        Retrieves tasks assigned to a specific performer within a team.

        Args:
            performer_id (int): ID of the performer.
            team_id (int): ID of the team.

        Returns:
            list[TaskSchema]: List of TaskSchema objects. Each task includes its evaluation value
            if it exists.
        """
        tasks = await self.manager.get_tasks_by_performer(performer_id, team_id)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def update_task(self, task_data: TaskUpdateSchema, task_id: int, team_id: int) -> TaskUpdateSuccessSchema:
        """
        Updates an existing task.

        Args:
            task_data (TaskUpdateSchema): Data to update the task with.
            task_id (int): ID of the task to update.
            team_id (int): ID of the team the task belongs to.

        Returns:
            TaskUpdateSuccessSchema: Confirmation schema.

        Raises:
            HTTPException: If the task is not found or an error occurs during update.
        """
        try:
            task = await self.manager.update_task(task_data, task_id, team_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='The task was not found',
                )
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{e}',
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when updating the task',
            )

        return TaskUpdateSuccessSchema()

    async def delete_task(self, task_id: int, team_id: int) -> None:
        """
        Deletes a task by its ID.

        Args:
            task_id (int): ID of the task to delete.
            team_id (int): ID of the team the task belongs to.

        Raises:
            HTTPException: If the task is not found or deletion fails.
        """
        try:
            deleted = await self.manager.delete_task(task_id, team_id)
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{e}',
            )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The task was not found',
            )

    async def update_task_evaluation(
        self, task_id: int, team_id: int, evaluator_id: int, evaluation_data: EvaluationSchema
    ) -> EvaluationSuccessSchema:
        """
        Updates an existing evaluation of a task or creates it if it does not exist.

        Args:
            task_id (int): ID of the task.
            team_id (int): ID of the team the task belongs to.
            evaluator_id (int): ID of the evaluator performing the evaluation.
            evaluation_data (EvaluationSchema): New evaluation data (value).

        Returns:
            EvaluationSuccessSchema: Confirmation schema indicating the evaluation was successfully
            created or updated.

        Raises:
            HTTPException:
                - 404 if the task does not exist.
                - 403 if the task not in the team.
                - 400 if a unique evaluation constraint is violated or another database error occurs.
        """
        try:
            await self.manager.update_task_evaluation(task_id, team_id, evaluator_id, evaluation_data)
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{e}',
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when updating the task evaluation',
            )

        return EvaluationSuccessSchema()


def get_task_service(manager: Annotated[TaskManager, Depends(get_task_manager)]) -> TaskService:
    """
    Dependency injector for TaskService.

    Args:
        manager (TaskManager): Injected TaskManager instance.

    Returns:
        TaskService: Initialized TaskService instance.
    """
    return TaskService(manager=manager)
