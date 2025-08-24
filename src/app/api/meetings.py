from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_manager, require_user
from app.models.users import User
from app.schemas.meetings import (
    MeetingCreateSchema,
    MeetingCreateSuccessSchema,
    MeetingSchema,
    MeetingUpdateSchema,
    MeetingUpdateSuccessSchema,
)
from app.services.meetings import MeetingService, get_meeting_service

meetings_router = APIRouter(prefix='/{team_id:int}/meetings', tags=['meetings'])


@meetings_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_meeting(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_data: MeetingCreateSchema,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> MeetingCreateSuccessSchema:
    return await service.create_meeting(meeting_data, team_id)


@meetings_router.get('/')
async def get_meetings_by_team(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[MeetingSchema]:
    return await service.get_meetings_by_team(team_id)


@meetings_router.get('/mine')
async def get_my_meetings_in_team(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[MeetingSchema]:
    return await service.get_meetings_by_member(member.id, team_id)


@meetings_router.put('/{meeting_id:int}')
async def update_meeting(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_data: MeetingUpdateSchema,
    meeting_id: int,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> MeetingUpdateSuccessSchema:
    return await service.update_meeting(meeting_data, meeting_id, team_id)


@meetings_router.delete('/{meeting_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_manager)],
):
    await service.delete_meeting(meeting_id)
