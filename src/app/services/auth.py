from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import TokenMixin
from app.managers.users import UserManager, get_user_manager
from app.schemas.auth import CredentialsSchema, TokenSchema


class AuthService(TokenMixin):
    """
    Service for handling user authentication and token generation.

    Attributes:
        manager (UserManager): An instance of UserManager to handle user-related operations.

    Methods:
        authenticate(credentials: CredentialsSchema) -> TokenSchema:
            Verifies user credentials and generates an access token.
    """

    def __init__(self, manager: UserManager):
        """
        Initializes the AuthService with a UserManager instance.

        Args:
            manager (UserManager): User manager for user-related operations.
        """
        self.manager = manager

    async def authenticate(self, credentials: CredentialsSchema) -> TokenSchema:
        """
        Authenticates a user by their credentials and returns a JWT access token.

        Args:
            credentials (CredentialsSchema): User credentials containing email and password.

        Raises:
            HTTPException: If the user does not exist or the credentials are invalid (status 401).

        Returns:
            TokenSchema: A schema containing the generated JWT access token.
        """
        is_user_exists = await self.manager.check_user_by_credentials(credentials)

        if not is_user_exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password',
            )

        access_token = self.generate_access_token(email=credentials.email)
        return TokenSchema(access_token=access_token)


def get_auth_service(manager: Annotated[UserManager, Depends(get_user_manager)]) -> AuthService:
    """
    Dependency injector for AuthService.

    Args:
        manager (UserManager): Injected UserManager instance.

    Returns:
        AuthService: Initialized AuthService instance.
    """
    return AuthService(manager=manager)
