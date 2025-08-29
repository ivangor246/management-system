from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.comments import Comment
from app.schemas.comments import CommentCreateSchema


class CommentManager:
    """Manager for handling task comments.

    Provides operations for creating, retrieving, and deleting comments.
    """

    def __init__(self, session: AsyncSession):
        """Initialize CommentManager.

        Args:
            session (AsyncSession): SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create_comment(self, comment_data: CommentCreateSchema, user_id: int, task_id: int) -> Comment:
        """Create a new comment for a task.

        Args:
            comment_data (CommentCreateSchema): Data for creating a comment.
            user_id (int): ID of the user who created the comment.
            task_id (int): ID of the related task.

        Returns:
            Comment: The created comment instance.

        Raises:
            SQLAlchemyError: If an error occurs while committing to the database.
        """
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

    async def get_comments_by_task(self, task_id: int) -> list[Comment]:
        """Retrieve all comments for a given task.

        Args:
            task_id (int): The ID of the task.

        Returns:
            list[Comment]: A list of comments ordered by creation date.
        """
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_comment(self, comment_id: int) -> bool:
        """Delete a comment by its ID and related task ID.

        Args:
            comment_id (int): The ID of the comment to delete.
            task_id (int): The ID of the related task.

        Returns:
            bool: True if the comment was found and deleted, False otherwise.

        Raises:
            SQLAlchemyError: If an error occurs while committing the deletion.
        """
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.session.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment:
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
