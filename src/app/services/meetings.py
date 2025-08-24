from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.meetings import MeetingManager, get_meeting_manager
from app.schemas.meetings import (
    MeetingCreateSchema,
    MeetingCreateSuccessSchema,
    MeetingSchema,
    MeetingUpdateSchema,
    MeetingUpdateSuccessSchema,
)


class MeetingService:
    def __init__(self, manager: MeetingManager):
        self.manager = manager

    async def create_meeting(self, meeting_data: MeetingCreateSchema, team_id: int) -> MeetingCreateSuccessSchema:
        try:
            new_meeting = await self.manager.create_meeting(meeting_data, team_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when creating the meeting',
            )
        return MeetingCreateSuccessSchema(meeting_id=new_meeting.id)

    async def get_meetings_by_team(self, team_id: int) -> list[MeetingSchema]:
        meetings = await self.manager.get_meetings_by_team(team_id)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def get_meetings_by_member(self, member_id: int, team_id: int) -> list[MeetingSchema]:
        meetings = await self.manager.get_meetings_by_member(member_id, team_id)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def update_meeting(
        self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int
    ) -> MeetingUpdateSuccessSchema:
        try:
            meeting = await self.manager.update_meeting(meeting_data, meeting_id, team_id)
            if not meeting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='The meeting was not found',
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong when updating the meeting',
            )

        return MeetingUpdateSuccessSchema()

    async def delete_meeting(self, meeting_id: int) -> None:
        deleted = await self.manager.delete_meeting(meeting_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The meeting was not found',
            )


def get_meeting_service(manager: Annotated[MeetingManager, Depends(get_meeting_manager)]) -> MeetingService:
    return MeetingService(manager=manager)
