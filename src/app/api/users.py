from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user
from app.models.users import User
from app.schemas.users import UserSchema, UserUpdateSchema, UserUpdateSuccessSchema
from app.services.users import UserService, get_user_service

users_router = APIRouter(prefix='/users', tags=['users'])


@users_router.get('/me')
async def get_user_data(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
) -> UserSchema:
    """
    Retrieve the current authenticated user's data.

    Args:
        service (UserService): User service dependency.
        auth_user (User): Current authenticated user.

    Returns:
        UserSchema: User details including username, email, and profile information.
    """
    return await service.get_user_data(auth_user)


@users_router.put('/me')
async def update_user(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
    user_data: UserUpdateSchema,
) -> UserUpdateSuccessSchema:
    """
    Update the current authenticated user's profile.

    Args:
        service (UserService): User service dependency.
        auth_user (User): Current authenticated user.
        user_data (UserUpdateSchema): New user information.

    Returns:
        UserUpdateSuccessSchema: Confirmation of a successful update.
    """
    return await service.update_user(auth_user, user_data)


@users_router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
):
    """
    Delete the current authenticated user's account.

    Args:
        service (UserService): User service dependency.
        auth_user (User): Current authenticated user.

    Returns:
        None
    """
    await service.delete_user(auth_user)
