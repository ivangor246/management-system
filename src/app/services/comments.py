from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.comments import CommentManager, get_comment_manager
from app.schemas.comments import CommentCreateSchema, CommentCreateSuccessSchema, CommentSchema


class CommentService:
    def __init__(self, manager: CommentManager):
        self.manager = manager

    async def create_comment(
        self, comment_data: CommentCreateSchema, user_id: int, task_id: int
    ) -> CommentCreateSuccessSchema:
        try:
            new_comment = await self.manager.create_comment(comment_data, user_id, task_id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when creating the comment',
            )
        return CommentCreateSuccessSchema(comment_id=new_comment.id)

    async def get_comments_by_task(self, task_id: int) -> list[CommentSchema]:
        comments = await self.manager.get_comments_by_task(task_id)
        return [CommentSchema.model_validate(comment) for comment in comments]

    async def delete_comment(self, comment_id: int, task_id: int) -> None:
        deleted = await self.manager.delete_comment(comment_id, task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The comment was not found',
            )


def get_comment_service(manager: Annotated[CommentManager, Depends(get_comment_manager)]) -> CommentService:
    return CommentService(manager=manager)
