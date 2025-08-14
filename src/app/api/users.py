from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user
from app.models.users import User
from app.schemas.users import UserSchema, UserUpdateSchema, UserUpdateSuccessSchema
from app.services.users import UserService, get_user_service

users_router = APIRouter(prefix='/users', tags=['users'])


@users_router.get('/')
async def get_user_data(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
) -> UserSchema:
    return await service.get_user_data(auth_user)


@users_router.put('/')
async def update_user(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
    user_data: UserUpdateSchema,
) -> UserUpdateSuccessSchema:
    response = await service.update_user(auth_user, user_data)
    return response


@users_router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
):
    await service.delete_user(auth_user)
