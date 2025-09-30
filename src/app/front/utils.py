from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_request_user

http_bearer = HTTPBearer(auto_error=False)


async def get_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> dict:
    context = {
        'is_auth': False,
        'user': None,
    }

    try:
        user = await get_request_user(request, session, credentials)
    except HTTPException:
        user = None

    if user:
        context['is_auth'] = True
        context['user'] = user

    request.state.context = context
    return context
