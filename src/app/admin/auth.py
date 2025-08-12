from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from app.core.database import session_factory
from app.core.security import HashingMixin
from app.models.users import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
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
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return 'user_id' in request.session
