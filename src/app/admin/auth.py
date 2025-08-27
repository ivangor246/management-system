"""
Admin authentication backend for SQLAdmin.

Provides login, logout, and session-based authentication for admin users.
"""

from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from app.core.database import session_factory
from app.core.security import HashingMixin
from app.models.users import User


class AdminAuth(AuthenticationBackend):
    """
    SQLAdmin authentication backend for verifying admin users.
    """

    async def login(self, request: Request) -> bool:
        """
        Authenticate an admin user using form data.

        Args:
            request (Request): FastAPI request containing form data with 'username' and 'password'.

        Returns:
            bool: True if authentication succeeds, False otherwise.
        """
        form = await request.form()
        username = form.get('username')
        password = form.get('password')

        async with session_factory() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if (not user) or (not user.is_admin) or (not HashingMixin.verify_password(password, user.hashed_password)):
                return False

        request.session.update({'user_id': user.id})
        return True

    async def logout(self, request: Request) -> bool:
        """
        Logout the currently authenticated admin user by clearing the session.

        Args:
            request (Request): FastAPI request.

        Returns:
            bool: Always True.
        """
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Check if the current request has an authenticated admin session.

        Args:
            request (Request): FastAPI request.

        Returns:
            bool: True if 'user_id' is in session, False otherwise.
        """
        return 'user_id' in request.session
