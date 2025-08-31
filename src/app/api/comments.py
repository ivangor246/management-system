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
    """
    Create a new comment for a specific task.

    Args:
        service (CommentService): Comment service dependency.
        comment_data (CommentCreateSchema): Data for the new comment.
        task_id (int): ID of the task to attach the comment to.
        team_id (int): ID of the team the task belongs to.
        member (User): Authenticated user creating the comment.

    Returns:
        CommentCreateSuccessSchema: The created comment's ID.
    """
    return await service.create_comment(comment_data, member.id, task_id)


@comments_router.get('/')
async def get_comments_by_task(
    service: Annotated[CommentService, Depends(get_comment_service)],
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[CommentSchema]:
    """
    Retrieve all comments for a specific task.

    Args:
        service (CommentService): Comment service dependency.
        task_id (int): ID of the task to fetch comments for.
        team_id (int): ID of the team the task belongs to.
        member (User): Authenticated user requesting comments.

    Returns:
        List[CommentSchema]: A list of comments for the specified task.
    """
    return await service.get_comments_by_task(task_id)


@comments_router.delete('/{comment_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    service: Annotated[CommentService, Depends(get_comment_service)],
    comment_id: int,
    task_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
):
    """
    Delete a comment by its ID for a specific task.

    Args:
        service (CommentService): Comment service dependency.
        comment_id (int): ID of the comment to delete.
        task_id (int): ID of the task the comment belongs to.
        team_id (int): ID of the team the task belongs to.
        member (User): Authenticated user performing the deletion.
    """
    await service.delete_comment(comment_id)
