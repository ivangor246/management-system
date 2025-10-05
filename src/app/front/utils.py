from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.security import get_request_user
from app.models.meetings import Meeting
from app.models.tasks import Task
from app.models.teams import UserTeam
from app.schemas.meetings import MeetingSchema
from app.schemas.tasks import TaskSchema
from app.schemas.teams import UserRoles

http_bearer = HTTPBearer(auto_error=False)


async def get_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> dict:
    context = {
        'is_auth': False,
        'user': None,
        'error': False,
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


async def get_team_role(
    session: AsyncSession,
    user_id: int,
    team_id: int,
) -> UserRoles:
    stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
    result = await session.execute(stmt)
    association = result.scalar_one_or_none()
    return association.role


async def get_task_by_id(
    session: AsyncSession,
    task_id: int,
) -> TaskSchema:
    stmt = select(Task).where(Task.id == task_id).options(selectinload(Task.evaluation))
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    return TaskSchema.model_validate(task)


async def get_meeting_by_id(
    session: AsyncSession,
    meeting_id: int,
) -> TaskSchema:
    stmt = select(Meeting).where(Meeting.id == meeting_id)
    result = await session.execute(stmt)
    meeting = result.scalar_one_or_none()
    return MeetingSchema.model_validate(meeting)
