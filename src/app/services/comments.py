from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.comments import CommentManager, get_comment_manager
from app.schemas.comments import CommentCreateSchema, CommentCreateSuccessSchema, CommentSchema


class CommentService:
    """
    Service to handle operations related to comments, including creation, retrieval, and deletion.

    Attributes:
        manager (CommentManager): Manager responsible for comment database operations.

    Methods:
        create_comment(comment_data: CommentCreateSchema, user_id: int, task_id: int) -> CommentCreateSuccessSchema:
            Creates a new comment for a specific task by a user.
        get_comments_by_task(task_id: int) -> list[CommentSchema]:
            Retrieves all comments associated with a specific task.
        delete_comment(comment_id: int, task_id: int) -> None:
            Deletes a comment from a task. Raises HTTPException if not found.
    """

    def __init__(self, manager: CommentManager):
        """
        Initializes the CommentService with a CommentManager.

        Args:
            manager (CommentManager): The manager instance for handling comment operations.
        """
        self.manager = manager

    async def create_comment(
        self, comment_data: CommentCreateSchema, user_id: int, task_id: int
    ) -> CommentCreateSuccessSchema:
        """
        Creates a new comment for a task.

        Args:
            comment_data (CommentCreateSchema): Data required to create the comment.
            user_id (int): ID of the user creating the comment.
            task_id (int): ID of the task the comment belongs to.

        Returns:
            CommentCreateSuccessSchema: Schema containing the ID of the created comment.

        Raises:
            HTTPException: If there is an error during comment creation.
        """
        try:
            new_comment = await self.manager.create_comment(comment_data, user_id, task_id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when creating the comment',
            )
        return CommentCreateSuccessSchema(comment_id=new_comment.id)

    async def get_comments_by_task(self, task_id: int) -> list[CommentSchema]:
        """
        Retrieves all comments for a specific task.

        Args:
            task_id (int): ID of the task to fetch comments for.

        Returns:
            list[CommentSchema]: List of comment schemas.
        """
        comments = await self.manager.get_comments_by_task(task_id)
        return [CommentSchema.model_validate(comment) for comment in comments]

    async def delete_comment(self, comment_id: int, task_id: int) -> None:
        """
        Deletes a comment from a task.

        Args:
            comment_id (int): ID of the comment to delete.
            task_id (int): ID of the task the comment belongs to.

        Raises:
            HTTPException: If the comment does not exist.
        """
        deleted = await self.manager.delete_comment(comment_id, task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The comment was not found',
            )


def get_comment_service(manager: Annotated[CommentManager, Depends(get_comment_manager)]) -> CommentService:
    """
    Dependency injector for CommentService.

    Args:
        manager (CommentManager): Injected CommentManager instance.

    Returns:
        CommentService: Initialized CommentService instance.
    """
    return CommentService(manager=manager)
