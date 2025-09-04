from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_manager, require_member
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
    """
    Create a new meeting for a team.

    Args:
        service (MeetingService): Meeting service dependency.
        meeting_data (MeetingCreateSchema): Data for creating the meeting.
        team_id (int): ID of the team the meeting belongs to.
        manager (User): Authenticated user with manager or admin role.

    Returns:
        MeetingCreateSuccessSchema: The created meeting's ID.
    """
    return await service.create_meeting(meeting_data, team_id)


@meetings_router.get('/')
async def get_meetings_by_team(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> list[MeetingSchema]:
    """
    Get all meetings for a specific team.

    Args:
        service (MeetingService): Meeting service dependency.
        team_id (int): ID of the team to retrieve meetings for.
        member (User): Authenticated user who is a member of the team.

    Returns:
        List[MeetingSchema]: List of meetings for the team.
    """
    return await service.get_meetings_by_team(team_id)


@meetings_router.get('/mine')
async def get_my_meetings_in_team(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> list[MeetingSchema]:
    """
    Get meetings in a team where the authenticated user is a participant.

    Args:
        service (MeetingService): Meeting service dependency.
        team_id (int): ID of the team.
        member (User): Authenticated user.

    Returns:
        List[MeetingSchema]: List of meetings the user participates in.
    """
    return await service.get_meetings_by_member(member.id, team_id)


@meetings_router.put('/{meeting_id:int}')
async def update_meeting(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_data: MeetingUpdateSchema,
    meeting_id: int,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
) -> MeetingUpdateSuccessSchema:
    """
    Update a meeting in a team.

    Args:
        service (MeetingService): Meeting service dependency.
        meeting_data (MeetingUpdateSchema): Updated data for the meeting.
        meeting_id (int): ID of the meeting to update.
        team_id (int): ID of the team the meeting belongs to.
        manager (User): Authenticated user with manager or admin role.

    Returns:
        MeetingUpdateSuccessSchema: Success response.
    """
    return await service.update_meeting(meeting_data, meeting_id, team_id)


@meetings_router.delete('/{meeting_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_id: int,
    team_id: int,
    member: Annotated[User, Depends(require_manager)],
):
    """
    Delete a meeting from a team.

    Args:
        service (MeetingService): Meeting service dependency.
        meeting_id (int): ID of the meeting to delete.
        team_id (int): ID of the team the meeting belongs to.
        member (User): Authenticated user with manager or admin role.
    """
    await service.delete_meeting(meeting_id)
