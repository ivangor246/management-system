from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.comments import Comment
from app.schemas.comments import CommentCreateSchema


class CommentManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_comment(self, comment_data: CommentCreateSchema, user_id: int, task_id: int) -> Comment:
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
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        result = await self.session.execute(stmt)
        return result.scalars()

    async def delete_comment(self, comment_id: int, task_id: int) -> bool:
        stmt = select(Comment).where(Comment.id == comment_id, Comment.task_id == task_id)
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
    return CommentManager(session=session)
