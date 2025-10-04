from pydantic import EmailStr, Field

from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema, BaseUpdateSchema


class UserSchema(BaseModelSchema):
    username: str
    email: EmailStr
    first_name: str
    last_name: str | None
    is_admin: bool


class UserCreateSchema(BaseCreateSchema):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str | None = Field(None, min_length=2, max_length=100)


class UserCreateSuccessSchema(BaseResponseSchema):
    user_id: int
    detail: str = 'The user has been successfully created'


class UserUpdateSchema(BaseUpdateSchema):
    username: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6)
    first_name: str | None = Field(None, min_length=2, max_length=100)
    last_name: str | None = Field(None, min_length=2, max_length=100)


class UserUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The user has been successfully updated'
