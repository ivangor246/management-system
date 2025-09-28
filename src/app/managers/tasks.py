from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.evaluations import Evaluation
from app.models.tasks import Task
from app.models.teams import UserTeam
from app.schemas.evaluations import EvaluationSchema
from app.schemas.tasks import TaskCreateSchema, TaskUpdateSchema


class TaskManager:
    """Manager class responsible for handling task-related operations in the database."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the TaskManager with a database session.

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session for database interaction.
        """
        self.session = session

    def __check_deadline(self, deadline: date):
        if deadline < datetime.now(timezone.utc).date():
            raise ValueError('Deadline cannot be in the past')

    async def __check_task_in_team(self, task_id: int, team_id: int):
        """
        Check whether a task exists and belongs to the given team.

        Args:
            task_id (int): ID of the task to check.
            team_id (int): ID of the team to validate against.

        Raises:
            LookupError: If the task is not found.
            PermissionError: If the task does not belong to the given team.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise LookupError('Task not found')

        if task.team_id != team_id:
            raise PermissionError('Task does not belong to the team')

    async def __check_user_in_team(self, user_id: int, team_id: int):
        """
        Check whether a user belongs to the given team.

        Args:
            user_id (int): ID of the user to check.
            team_id (int): ID of the team to validate against.

        Raises:
            LookupError: If the user is not found in the team.
        """
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise LookupError('User not found in this team')

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> Task:
        """
        Create a new task in the database.

        Args:
            task_data (TaskCreateSchema): Data required to create a new task.
            team_id (int): ID of the team associated with the task.

        Returns:
            Task: The newly created task object.

        Raises:
            ValueError: If deadline is in the past.
            SQLAlchemyError: If commit or refresh fails.
        """
        self.__check_deadline(task_data.deadline)

        await self.__check_user_in_team(task_data.performer_id, team_id)

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
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return new_task

    async def get_tasks_by_team(self, team_id: int, limit: int = 0, offset: int = 0) -> list[Task]:
        """
        Retrieve all tasks for a given team, including associated evaluation objects.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[Task]: List of Task objects. Each Task includes its evaluation if present.
        """
        stmt = select(Task).where(Task.team_id == team_id).options(selectinload(Task.evaluation))
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_tasks_by_performer(
        self, performer_id: int, team_id: int, limit: int = 0, offset: int = 0
    ) -> list[Task]:
        """
        Retrieve all tasks for a specific performer within a team, including evaluations.

        Args:
            performer_id (int): ID of the performer.
            team_id (int): ID of the team.

        Returns:
            list[Task]: List of Task objects assigned to the performer. Each Task includes
            its evaluation if present.
        """
        stmt = (
            select(Task)
            .where(Task.performer_id == performer_id, Task.team_id == team_id)
            .options(selectinload(Task.evaluation))
        )
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_task(self, task_data: TaskUpdateSchema, task_id: int, team_id: int) -> Task | None:
        """
        Update an existing task.

        Args:
            task_data (TaskUpdateSchema): Fields to update.
            task_id (int): ID of the task to update.
            team_id (int): ID of the team the task belongs to.

        Returns:
            Task | None: Updated task object if found, otherwise None.

        Raises:
            ValueError: If deadline is in the past.
            SQLAlchemyError: If commit or refresh fails.
        """
        if task_data.deadline is not None:
            self.__check_deadline(task_data.deadline)

        await self.__check_task_in_team(task_id, team_id)

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
            await self.__check_user_in_team(task_data.performer_id, team_id)
            task.performer_id = task_data.performer_id

        try:
            await self.session.commit()
            await self.session.refresh(task)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return task

    async def delete_task(self, task_id: int, team_id: int) -> bool:
        """
        Delete a task by its ID.

        Args:
            task_id (int): ID of the task to delete.
            team_id (int): ID of the team the task belongs to.

        Returns:
            bool: True if task was deleted, False if task was not found.

        Raises:
            SQLAlchemyError: If commit fails.
        """
        await self.__check_task_in_team(task_id, team_id)

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

    async def update_task_evaluation(
        self,
        task_id: int,
        team_id: int,
        evaluator_id: int,
        evaluation_data: EvaluationSchema,
    ) -> Evaluation:
        """
        Update or create the evaluation of a task.

        Args:
            task_id (int): ID of the task to update.
            team_id (int): ID of the team the task belongs to.
            evaluator_id (int): ID of the evaluator.
            evaluation_data (EvaluationSchema): New evaluation data.

        Returns:
            Evaluation: Updated or created evaluation object if successful.
        """
        await self.__check_task_in_team(task_id, team_id)

        stmt = select(Evaluation).where(Evaluation.task_id == task_id)
        result = await self.session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if evaluation:
            evaluation.value = evaluation_data.value
            evaluation.evaluator_id = evaluator_id
        else:
            evaluation = Evaluation(
                value=evaluation_data.value,
                evaluator_id=evaluator_id,
                task_id=task_id,
            )
            self.session.add(evaluation)

        try:
            await self.session.commit()
            await self.session.refresh(evaluation)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return evaluation


def get_task_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskManager:
    """
    Dependency function to provide a TaskManager instance.

    Args:
        session (AsyncSession): SQLAlchemy asynchronous session.

    Returns:
        TaskManager: An instance of TaskManager.
    """
    return TaskManager(session=session)
