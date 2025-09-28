from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import HashingMixin
from app.models.users import User
from app.schemas.auth import CredentialsSchema
from app.schemas.users import UserCreateSchema, UserUpdateSchema


class UserManager(HashingMixin):
    """
    Manager class for user-related operations.

    Provides methods to create, update, delete users,
    and validate user credentials.

    Inherits:
        HashingMixin: Provides password hashing and verification utilities.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize UserManager with an asynchronous database session.

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session.
        """
        self.session = session

    async def create_user(self, user_data: UserCreateSchema) -> User:
        """
        Create a new user and persist it to the database.

        Args:
            user_data (UserCreateSchema): Pydantic schema with user creation data.

        Returns:
            User: The newly created user instance.

        Raises:
            IntegrityError: If a user with the same email or username already exists.
        """
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_admin=False,
        )
        self.session.add(new_user)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

        await self.session.refresh(new_user)
        return new_user

    async def check_user_by_credentials(self, credentials: CredentialsSchema) -> bool:
        """
        Verify user credentials by email and password.

        Args:
            credentials (CredentialsSchema): User credentials schema.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        stmt = select(User).where(User.email == credentials.email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(credentials.password, user.hashed_password):
            return False

        return True

    async def update_user(self, user: User, user_data: UserUpdateSchema) -> User:
        """
        Update an existing user with new values.

        Args:
            user (User): The user instance to update.
            user_data (UserUpdateSchema): Pydantic schema with updated fields.

        Returns:
            User: The updated user instance.

        Raises:
            IntegrityError: If updated values violate unique constraints (e.g., duplicate email/username).
        """
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.hashed_password = self.hash_password(user_data.password)
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

        await self.session.refresh(user)
        return user

    async def delete_user(self, user: User) -> None:
        """
        Permanently delete a user from the database.

        Args:
            user (User): The user instance to delete.

        Returns:
            None
        """
        await self.session.delete(user)
        await self.session.commit()


def get_user_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> UserManager:
    """
    Dependency provider for UserManager.

    Args:
        session (AsyncSession): SQLAlchemy asynchronous session dependency.

    Returns:
        UserManager: Instance of UserManager with the provided session.
    """
    return UserManager(session=session)
