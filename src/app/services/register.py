from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.managers.users import UserManager, get_user_manager
from app.schemas.users import UserCreateSchema, UserCreateSuccessSchema


class RegisterService:
    """
    Service responsible for registering new users.

    Attributes:
        manager (UserManager): Manager responsible for user database operations.

    Methods:
        register_user(user_data: UserCreateSchema) -> UserCreateSuccessSchema:
            Registers a new user and returns the created user's ID.
    """

    def __init__(self, manager: UserManager):
        """
        Initializes the RegisterService with a UserManager.

        Args:
            manager (UserManager): The manager instance for handling user operations.
        """
        self.manager = manager

    async def register_user(self, user_data: UserCreateSchema) -> UserCreateSuccessSchema:
        """
        Registers a new user in the system.

        Args:
            user_data (UserCreateSchema): Data required to create the new user.

        Returns:
            UserCreateSuccessSchema: Schema containing the ID of the newly created user.

        Raises:
            HTTPException: If a user with the same email or username already exists.
        """
        try:
            new_user = await self.manager.create_user(user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this email or username already exists',
            )

        return UserCreateSuccessSchema(user_id=new_user.id)


def get_register_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> RegisterService:
    """
    Dependency injector for RegisterService.

    Args:
        manager (UserManager): Injected UserManager instance.

    Returns:
        RegisterService: Initialized RegisterService instance.
    """
    return RegisterService(manager=manager)
