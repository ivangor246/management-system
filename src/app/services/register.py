from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.managers.users import UserManager, get_user_manager
from app.schemas.users import UserCreateSchema, UserCreateSuccessSchema


class RegisterService:
    def __init__(self, manager: UserManager):
        self.manager = manager

    async def register_user(self, user_data: UserCreateSchema) -> UserCreateSuccessSchema:
        try:
            new_user = await self.manager.create_user(user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this email or username already exists',
            )

        return UserCreateSuccessSchema(user_id=new_user.id)


def get_register_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> RegisterService:
    return RegisterService(manager=manager)
