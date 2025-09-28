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
    Service layer responsible for handling task-related operations within a team.

    Attributes:
        manager (TaskManager): Manager responsible for database operations on tasks.

    Methods:
        create_task(task_data: TaskCreateSchema, team_id: int) -> TaskCreateSuccessSchema:
            Creates a new task for the specified team.
        get_tasks_by_team(team_id: int) -> list[TaskSchema]:
            Retrieves all tasks for a given team.
        get_tasks_by_performer(performer_id: int, team_id: int) -> list[TaskSchema]:
            Retrieves tasks assigned to a specific performer within a team.
        update_task(task_id: int, task_data: TaskUpdateSchema) -> TaskUpdateSuccessSchema:
            Updates an existing task.
        delete_task(task_id: int, team_id: int) -> None:
            Deletes a task by its ID.
        update_task_evaluation(task_id: int, team_id: int, evaluator_id: int, evaluation_data: EvaluationSchema) -> EvaluationSuccessSchema:
            Updates or creates an evaluation for a specific task.
    """

    def __init__(self, manager: TaskManager):
        """
        Initialize the TaskService with a TaskManager.

        Args:
            manager (TaskManager): Manager instance for handling task operations.
        """
        self.manager = manager

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> TaskCreateSuccessSchema:
        """
        Create a new task for the specified team.

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
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
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

    async def get_tasks_by_team(self, team_id: int, limit: int = 0, offset: int = 0) -> list[TaskSchema]:
        """
        Retrieve all tasks for a given team.

        Args:
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of tasks to retrieve. Defaults to 0 (no limit).
            offset (int, optional): Number of tasks to skip before returning results. Defaults to 0.

        Returns:
            list[TaskSchema]: List of TaskSchema objects including evaluation if it exists.
        """
        tasks = await self.manager.get_tasks_by_team(team_id, limit, offset)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def get_tasks_by_performer(
        self, performer_id: int, team_id: int, limit: int = 0, offset: int = 0
    ) -> list[TaskSchema]:
        """
        Retrieve tasks assigned to a specific performer within a team.

        Args:
            performer_id (int): ID of the performer.
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of tasks to retrieve. Defaults to 0 (no limit).
            offset (int, optional): Number of tasks to skip before returning results. Defaults to 0.

        Returns:
            list[TaskSchema]: List of TaskSchema objects including evaluation if it exists.
        """
        tasks = await self.manager.get_tasks_by_performer(performer_id, team_id, limit, offset)
        return [TaskSchema.model_validate(task) for task in tasks]

    async def update_task(self, task_data: TaskUpdateSchema, task_id: int, team_id: int) -> TaskUpdateSuccessSchema:
        """
        Update an existing task.

        Args:
            task_data (TaskUpdateSchema): Data to update the task with.
            task_id (int): ID of the task to update.
            team_id (int): ID of the team the task belongs to.

        Returns:
            TaskUpdateSuccessSchema: Confirmation schema.

        Raises:
            HTTPException: If the task is not found, access is denied, or an error occurs.
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
        Delete a task by its ID.

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
        Update or create an evaluation for a task.

        Args:
            task_id (int): ID of the task.
            team_id (int): ID of the team the task belongs to.
            evaluator_id (int): ID of the evaluator performing the evaluation.
            evaluation_data (EvaluationSchema): Evaluation data.

        Returns:
            EvaluationSuccessSchema: Confirmation schema indicating evaluation was successfully created or updated.

        Raises:
            HTTPException: If an error occurs during evaluation update.
        """
        try:
            await self.manager.update_task_evaluation(task_id, team_id, evaluator_id, evaluation_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
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
