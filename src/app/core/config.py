from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    TITLE: str = 'Business Management System'
    DOCS_URL: str = '/api/docs'
    OPENAPI_URL: str = '/api/docs.json'
    DEBUG: bool = Field(alias='DEBUG') == 'True'

    SECRET_KEY: str = Field(alias='SECRET_KEY')
    TOKEN_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60

    DB_HOST: str = Field(alias='DB_HOST')
    DB_PORT: str = Field(alias='DB_PORT')
    DB_NAME: str = Field(alias='DB_NAME')
    DB_USER: str = Field(alias='DB_USER')
    DB_PASS: str = Field(alias='DB_PASS')

    @property
    def DB_URL(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


@lru_cache
def get_config() -> Config:
    config = Config()
    return config


config = get_config()
