import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.users import UserManager
from app.models.users import User
from app.schemas.auth import CredentialsSchema, TokenSchema
from app.schemas.users import UserCreateSchema
from app.services.auth import AuthService


@pytest.fixture
def user_data():
    return UserCreateSchema(
        username='username1',
        email='email1@email.com',
        password='password1',
        first_name='first_name1',
        last_name='last_name1',
    )


@pytest.fixture
def credentials():
    return CredentialsSchema(
        email='email1@email.com',
        password='password1',
    )


@pytest_asyncio.fixture
async def user(session: AsyncSession, user_data) -> User:
    user_manager = UserManager(session)
    new_user = await user_manager.create_user(user_data)
    return new_user


@pytest.mark.asyncio
class TestAuthService:
    async def test_authenticate(self, session: AsyncSession, credentials: CredentialsSchema, user: User):
        manager = UserManager(session)
        service = AuthService(manager)

        response = await service.authenticate(credentials)

        assert isinstance(response, TokenSchema)
        assert len(response.access_token) > 0

        payload = service.validate_token(response.access_token)
        assert service.get_email_from_payload(payload) == credentials.email

    async def test_authenticate_with_wrong_email(
        self, session: AsyncSession, credentials: CredentialsSchema, user: User
    ):
        manager = UserManager(session)
        service = AuthService(manager)

        wrong_credentials = credentials.model_copy()
        wrong_credentials.email = 'email2@email.com'

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate(wrong_credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_authenticate_with_wrong_password(
        self, session: AsyncSession, credentials: CredentialsSchema, user: User
    ):
        manager = UserManager(session)
        service = AuthService(manager)

        wrong_credentials = credentials.model_copy()
        wrong_credentials.password = 'password2'

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate(wrong_credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
