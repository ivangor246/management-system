from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.comments import Comment
from app.models.tasks import Task
from app.schemas.comments import CommentCreateSchema


class CommentManager:
    """
    Manager for handling task comments.

    Provides operations for creating, retrieving, and deleting comments.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize CommentManager.

        Args:
            session (AsyncSession): SQLAlchemy async session for database operations.
        """
        self.session = session

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
            raise LookupError('The task not found')

        if task.team_id != team_id:
            raise PermissionError('The task does not belong to the team')

    async def create_comment(
        self, comment_data: CommentCreateSchema, user_id: int, task_id: int, team_id: int
    ) -> Comment:
        """
        Create a new comment for a task.

        Args:
            comment_data (CommentCreateSchema): Data for creating a comment.
            user_id (int): ID of the user creating the comment.
            task_id (int): ID of the related task.
            team_id (int): ID of the team the task belongs to.

        Returns:
            Comment: The created comment instance.

        Raises:
            LookupError: If the task is not found.
            PermissionError: If the task does not belong to the given team.
            SQLAlchemyError: If an error occurs while committing to the database.
        """
        self.__check_task_in_team(task_id, team_id)

        new_comment = Comment(
            text=comment_data.text,
            user_id=user_id,
            task_id=task_id,
        )
        self.session.add(new_comment)

        try:
            await self.session.commit()
            await self.session.refresh(new_comment)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return new_comment

    async def get_comments_by_task(self, task_id: int, team_id: int) -> list[Comment]:
        """
        Retrieve all comments for a given task.

        Args:
            task_id (int): ID of the task to retrieve comments for.
            team_id (int): ID of the team the task belongs to.

        Returns:
            list[Comment]: A list of comments ordered by creation date.

        Raises:
            LookupError: If the task is not found.
            PermissionError: If the task does not belong to the given team.
        """
        self.__check_task_in_team(task_id, team_id)

        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_comment(self, comment_id: int, task_id: int, team_id: int) -> bool:
        """
        Delete a comment by its ID and related task ID.

        Args:
            comment_id (int): ID of the comment to delete.
            task_id (int): ID of the related task.
            team_id (int): ID of the team the task belongs to.

        Returns:
            bool: True if the comment was found and deleted, False otherwise.

        Raises:
            LookupError: If the task is not found.
            PermissionError: If the task does not belong to the given team.
            SQLAlchemyError: If an error occurs while committing the deletion.
        """
        self.__check_task_in_team(task_id, team_id)

        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.session.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment or comment.task_id != task_id:
            return False

        await self.session.delete(comment)
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True


def get_comment_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> CommentManager:
    """Dependency provider for CommentManager.

    Args:
        session (AsyncSession): SQLAlchemy async session.

    Returns:
        CommentManager: An instance of CommentManager.
    """
    return CommentManager(session=session)
