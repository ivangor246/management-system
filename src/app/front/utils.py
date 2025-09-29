from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.redis import redis
from app.core.security import TokenMixin
from app.models.users import User


async def get_context(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    token = request.cookies.get('access_token')
    context = {
        'is_auth': False,
        'user': None,
    }

    if token:
        user = await resolve_user_from_token(token, session)
        if user:
            context['is_auth'] = True
            context['user'] = user

    request.state.context = context
    return context


async def resolve_user_from_token(token: str, session: AsyncSession) -> User | None:
    if not token:
        return None

    if await redis.exists(f'bl:{token}'):
        return None

    token_mixin = TokenMixin()

    try:
        payload = token_mixin.validate_token(token)
    except Exception:
        return None

    if not payload:
        return None

    email = token_mixin.get_email_from_payload(payload)
    if not email:
        return None

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user
