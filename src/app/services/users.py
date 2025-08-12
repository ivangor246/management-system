from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.managers.users import UserManager, get_user_manager
from app.models.users import User
from app.schemas.users import UserSchema, UserUpdateSchema, UserUpdateSuccessSchema


class UserService:
    def __init__(self, manager: UserManager):
        self.manager = manager

    async def get_user_data(self, user: User) -> UserSchema:
        return UserSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            is_available=user.is_available,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_user(self, user: User, user_data: UserUpdateSchema) -> UserUpdateSuccessSchema:
        try:
            await self.manager.update_user(user, user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this email or username already exists',
            )

        return UserUpdateSuccessSchema()

    async def delete_user(self, user: User) -> None:
        await self.manager.delete_user(user)


def get_user_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> UserService:
    return UserService(manager=manager)
