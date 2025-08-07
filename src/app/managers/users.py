from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session


class UserManager:
    def __init__(self, session: AsyncSession):
        self.session = session


def get_user_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> UserManager:
    return UserManager(session=session)
