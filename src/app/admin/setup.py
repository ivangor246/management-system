from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import select

from app.core.config import config
from app.core.database import engine, session_factory
from app.core.security import HashingMixin
from app.models.users import User

from .auth import AdminAuth
from .views import CommentAdmin, MeetingAdmin, TaskAdmin, TeamAdmin, UserAdmin, UserTeamAdmin


async def create_admin_if_not_exists():
    async with session_factory() as session:
        stmt = select(User).where(User.username == config.ADMIN_NAME)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin is None:
            admin = User(
                username=config.ADMIN_NAME,
                email='admin@admin.com',
                hashed_password=HashingMixin.hash_password(config.ADMIN_PASS),
                first_name='admin',
                last_name=None,
                is_admin=True,
            )
            session.add(admin)
            await session.commit()


def init_admin(app: FastAPI):
    authentication_backend = AdminAuth(secret_key=config.SECRET_KEY)
    admin = Admin(app, engine, authentication_backend=authentication_backend)

    admin.add_view(CommentAdmin)
    admin.add_view(MeetingAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(UserTeamAdmin)
