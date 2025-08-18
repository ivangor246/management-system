from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_user
from app.models.users import User
from app.schemas.comments import CommentCreateSchema, CommentCreateSuccessSchema, CommentSchema
from app.services.comments import CommentService, get_comment_service

comments_router = APIRouter(prefix='/{task_id:int}/comments', tags=['comments'])


@comments_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_comment(
    service: Annotated[CommentService, Depends(get_comment_service)],
    comment_data: CommentCreateSchema,
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> CommentCreateSuccessSchema:
    return await service.create_comment(comment_data, member.id, task_id)


@comments_router.get('/')
async def get_comments_by_task(
    service: Annotated[CommentService, Depends(get_comment_service)],
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[CommentSchema]:
    return await service.get_comments_by_task(task_id)


@comments_router.delete('/{comment_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    service: Annotated[CommentService, Depends(get_comment_service)],
    comment_id: int,
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
):
    await service.delete_comment(comment_id, task_id)
