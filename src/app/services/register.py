from typing import Annotated

from fastapi import Depends

from app.managers.users import UserManager, get_user_manager


class RegisterService:
    def __init__(self, manager: UserManager):
        self.manager = manager


def get_user_service(manager: Annotated[UserManager, Depends(get_user_manager)]):
    return RegisterService(manager=manager)
