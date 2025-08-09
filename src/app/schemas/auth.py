from .base import BaseSchema


class CredentialsSchema(BaseSchema):
    email: str
    password: str


class TokenSchema(BaseSchema):
    access_token: str
    token_type: str = 'bearer'
