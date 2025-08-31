from pydantic import EmailStr

from .base import BaseSchema


class CredentialsSchema(BaseSchema):
    email: EmailStr
    password: str


class TokenSchema(BaseSchema):
    access_token: str
    token_type: str = 'bearer'
