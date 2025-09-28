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
    Manager for handling comments related to tasks.

    Provides operations for creating, retrieving, and deleting comments,
    as well as validating that a task belongs to a given team.
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
        Verify that a task exists and belongs to the given team.

        Args:
            task_id (int): ID of the task.
            team_id (int): ID of the team.

        Raises:
            LookupError: If the task does not exist.
            PermissionError: If the task belongs to another team.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise LookupError('Task not found')

        if task.team_id != team_id:
            raise PermissionError('Task does not belong to the given team')

    async def create_comment(
        self, comment_data: CommentCreateSchema, user_id: int, task_id: int, team_id: int
    ) -> Comment:
        """
        Create a new comment for a task.

        Args:
            comment_data (CommentCreateSchema): Data for creating the comment.
            user_id (int): ID of the user creating the comment.
            task_id (int): ID of the related task.
            team_id (int): ID of the team the task belongs to.

        Returns:
            Comment: The created comment instance.

        Raises:
            LookupError: If the task does not exist.
            PermissionError: If the task belongs to another team.
            SQLAlchemyError: If an error occurs during database commit.
        """
        await self.__check_task_in_team(task_id, team_id)

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

    async def get_comments_by_task(self, task_id: int, team_id: int, limit: int = 0, offset: int = 0) -> list[Comment]:
        """
        Retrieve comments for a given task.

        Args:
            task_id (int): ID of the task.
            team_id (int): ID of the team the task belongs to.
            limit (int, optional): Maximum number of comments to return. Defaults to 0 (no limit).
            offset (int, optional): Number of comments to skip for pagination. Defaults to 0.

        Returns:
            list[Comment]: A list of comments ordered by creation date.

        Raises:
            LookupError: If the task does not exist.
            PermissionError: If the task belongs to another team.
        """
        await self.__check_task_in_team(task_id, team_id)

        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_comment(self, comment_id: int, task_id: int, team_id: int) -> bool:
        """
        Delete a comment by its ID.

        Args:
            comment_id (int): ID of the comment to delete.
            task_id (int): ID of the related task.
            team_id (int): ID of the team the task belongs to.

        Returns:
            bool: True if the comment was found and deleted, False otherwise.

        Raises:
            LookupError: If the task does not exist.
            PermissionError: If the task belongs to another team.
            SQLAlchemyError: If an error occurs during database commit.
        """
        await self.__check_task_in_team(task_id, team_id)

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
    """
    Dependency provider for CommentManager.

    Args:
        session (AsyncSession): SQLAlchemy async session.

    Returns:
        CommentManager: An instance of CommentManager.
    """
    return CommentManager(session=session)
