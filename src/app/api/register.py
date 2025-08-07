from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.users import UserCreateSchema, UserCreateSuccessSchema
from app.services.register import RegisterService, get_register_service

register_router = APIRouter(prefix='/register')


@register_router.post('/', status_code=status.HTTP_201_CREATED)
async def register_user(
    service: Annotated[RegisterService, Depends(get_register_service)],
    user_data: UserCreateSchema,
) -> UserCreateSuccessSchema:
    return await service.register_user(user_data)
