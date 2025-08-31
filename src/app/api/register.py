from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.users import UserCreateSchema, UserCreateSuccessSchema
from app.services.register import RegisterService, get_register_service

register_router = APIRouter(prefix='/auth', tags=['auth'])


@register_router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(
    service: Annotated[RegisterService, Depends(get_register_service)],
    user_data: UserCreateSchema,
) -> UserCreateSuccessSchema:
    """
    Register a new user in the system.

    Args:
        service (RegisterService): Service responsible for user registration.
        user_data (UserCreateSchema): User information required for registration.

    Returns:
        UserCreateSuccessSchema: Contains the ID of the newly created user.

    Raises:
        HTTPException: If a user with the same email or username already exists.
    """
    return await service.register_user(user_data)
