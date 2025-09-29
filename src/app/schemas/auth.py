from pydantic import EmailStr

from .base import BaseResponseSchema, BaseSchema


class CredentialsSchema(BaseSchema):
    email: EmailStr
    password: str


class TokenSchema(BaseSchema):
    access_token: str
    token_type: str = 'bearer'


class LogoutSchema(BaseSchema):
    token: str


class LogoutSuccessSchema(BaseResponseSchema):
    detail: str = 'Successfully logged out'
