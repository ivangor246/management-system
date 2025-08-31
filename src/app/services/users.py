from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.managers.users import UserManager, get_user_manager
from app.models.users import User
from app.schemas.users import UserSchema, UserUpdateSchema, UserUpdateSuccessSchema


class UserService:
    """
    Service responsible for managing user-related operations, such as retrieving user data,
    updating user information, and deleting users.

    Attributes:
        manager (UserManager): Manager responsible for user database operations.

    Methods:
        get_user_data(user: User) -> UserSchema:
            Returns detailed information about a given user.
        update_user(user: User, user_data: UserUpdateSchema) -> UserUpdateSuccessSchema:
            Updates user information and handles possible integrity errors.
        delete_user(user: User) -> None:
            Deletes a user from the database.
    """

    def __init__(self, manager: UserManager):
        """
        Initializes the UserService with a UserManager.

        Args:
            manager (UserManager): The manager instance for handling user operations.
        """
        self.manager = manager

    async def get_user_data(self, user: User) -> UserSchema:
        """
        Retrieves detailed information for a specific user.

        Args:
            user (User): User instance to retrieve data from.

        Returns:
            UserSchema: Schema containing user's data.
        """
        return UserSchema.model_validate(user)

    async def update_user(self, user: User, user_data: UserUpdateSchema) -> UserUpdateSuccessSchema:
        """
        Updates information of a specific user.

        Args:
            user (User): User instance to update.
            user_data (UserUpdateSchema): Data for updating the user.

        Returns:
            UserUpdateSuccessSchema: Confirmation of successful update.

        Raises:
            HTTPException: If a user with the same email or username already exists.
        """
        try:
            await self.manager.update_user(user, user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this email or username already exists',
            )

        return UserUpdateSuccessSchema()

    async def delete_user(self, user: User) -> None:
        """
        Deletes a specific user from the database.

        Args:
            user (User): User instance to delete.
        """
        await self.manager.delete_user(user)


def get_user_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> UserService:
    """
    Dependency injector for UserService.

    Args:
        manager (UserManager): Injected UserManager instance.

    Returns:
        UserService: Initialized UserService instance.
    """
    return UserService(manager=manager)
