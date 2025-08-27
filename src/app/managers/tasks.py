from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.tasks import Task
from app.schemas.tasks import TaskCreateSchema, TaskScoreSchema, TaskUpdateSchema


class TaskManager:
    """Manager class responsible for handling task-related operations in the database."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the TaskManager with a database session.

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session for database interaction.
        """
        self.session = session

    async def create_task(self, task_data: TaskCreateSchema, team_id: int) -> Task:
        """
        Create a new task in the database.

        Args:
            task_data (TaskCreateSchema): Data required to create a new task.
            team_id (int): ID of the team associated with the task.

        Returns:
            Task: The newly created task object.

        Raises:
            Exception: If commit or refresh fails.
        """
        new_task = Task(
            description=task_data.description,
            deadline=task_data.deadline,
            status=task_data.status,
            performer_id=task_data.performer_id,
            team_id=team_id,
            score=None,
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
        """
        Retrieve all tasks for a given team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[Task]: List of tasks associated with the given team.
        """
        stmt = select(Task).where(Task.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalars()

    async def get_tasks_by_performer(self, performer_id: int, team_id: int) -> list[Task]:
        """
        Retrieve all tasks for a given performer within a team.

        Args:
            performer_id (int): ID of the performer.
            team_id (int): ID of the team.

        Returns:
            list[Task]: List of tasks assigned to the performer within the team.
        """
        stmt = select(Task).where(Task.performer_id == performer_id, Task.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalars()

    async def update_task(self, task_id: int, task_data: TaskUpdateSchema) -> Task | None:
        """
        Update an existing task.

        Args:
            task_id (int): ID of the task to update.
            task_data (TaskUpdateSchema): Fields to update.

        Returns:
            Task | None: Updated task object if found, otherwise None.

        Raises:
            SQLAlchemyError: If commit or refresh fails.
        """
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
        """
        Delete a task by its ID.

        Args:
            task_id (int): ID of the task to delete.

        Returns:
            bool: True if task was deleted, False if task was not found.

        Raises:
            SQLAlchemyError: If commit fails.
        """
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

    async def update_task_score(self, task_id: int, task_score: TaskScoreSchema) -> Task | None:
        """
        Update the score of a task.

        Args:
            task_id (int): ID of the task to update.
            task_score (TaskScoreSchema): New score to assign.

        Returns:
            Task | None: Updated task object if found, otherwise None.

        Raises:
            SQLAlchemyError: If commit or refresh fails.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return None

        task.score = task_score.score

        try:
            await self.session.commit()
            await self.session.refresh(task)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return task


def get_task_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskManager:
    """
    Dependency function to provide a TaskManager instance.

    Args:
        session (AsyncSession): SQLAlchemy asynchronous session.

    Returns:
        TaskManager: An instance of TaskManager.
    """
    return TaskManager(session=session)
