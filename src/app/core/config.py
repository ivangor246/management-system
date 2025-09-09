"""
Application configuration module.

This module defines the `Config` class for managing application settings
using environment variables and Pydantic's BaseSettings. It also provides
a cached instance of the configuration for reuse across the application.

Classes:
    Config(BaseSettings): Pydantic settings class with all application configuration.

Functions:
    get_config() -> Config: Returns a cached instance of the Config class.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Application configuration using environment variables.

    Attributes:
        TITLE (str): Application title for FastAPI docs.
        DOCS_URL (str): URL path for the Swagger UI documentation.
        OPENAPI_URL (str): URL path for the OpenAPI JSON schema.
        DEBUG (bool): Debug mode enabled if environment variable DEBUG is 'True'.
        SECRET_KEY (str): Secret key for JWT token generation.
        TOKEN_ALGORITHM (str): Algorithm used for JWT token encoding.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Expiration time of access tokens in minutes.
        DB_HOST (str): Database host address.
        DB_PORT (str): Database port.
        DB_NAME (str): Database name.
        DB_USER (str): Database username.
        DB_PASS (str): Database password.
        ADMIN_NAME (str): Admin username.
        ADMIN_PASS (str): Admin password.
    """

    TITLE: str = 'Business Management System'
    DOCS_URL: str = '/api/docs'
    OPENAPI_URL: str = '/api/docs.json'
    DEBUG: bool = Field(default=False, alias='DEBUG')

    SECRET_KEY: str = Field(alias='SECRET_KEY')
    TOKEN_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60

    DB_HOST: str = Field(alias='DB_HOST')
    DB_PORT: str = Field(alias='DB_PORT')
    DB_NAME: str = Field(alias='DB_NAME')
    DB_USER: str = Field(alias='DB_USER')
    DB_PASS: str = Field(alias='DB_PASS')

    ADMIN_NAME: str = Field(alias='ADMIN_NAME')
    ADMIN_PASS: str = Field(alias='ADMIN_PASS')

    REDIS_URL: str = 'redis://redis:6379/0'

    @property
    def DB_URL(self) -> str:
        """
        Constructs the async database connection URL.

        Returns:
            str: PostgreSQL async connection URL.
        """
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


@lru_cache
def get_config() -> Config:
    """
    Returns a cached instance of the Config class.

    Returns:
        Config: Cached configuration instance.
    """
    config = Config()
    return config


config = get_config()
