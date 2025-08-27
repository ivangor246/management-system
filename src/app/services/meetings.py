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
    """
    Service to handle operations related to meetings, including creation, retrieval, updating, and deletion.

    Attributes:
        manager (MeetingManager): Manager responsible for meeting database operations.

    Methods:
        create_meeting(meeting_data: MeetingCreateSchema, team_id: int) -> MeetingCreateSuccessSchema:
            Creates a new meeting for a specific team.
        get_meetings_by_team(team_id: int) -> list[MeetingSchema]:
            Retrieves all meetings for a specific team.
        get_meetings_by_member(member_id: int, team_id: int) -> list[MeetingSchema]:
            Retrieves all meetings for a specific member within a team.
        update_meeting(meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int) -> MeetingUpdateSuccessSchema:
            Updates an existing meeting. Raises HTTPException if not found.
        delete_meeting(meeting_id: int) -> None:
            Deletes a meeting by ID. Raises HTTPException if not found.
    """

    def __init__(self, manager: MeetingManager):
        """
        Initializes the MeetingService with a MeetingManager.

        Args:
            manager (MeetingManager): The manager instance for handling meeting operations.
        """
        self.manager = manager

    async def create_meeting(self, meeting_data: MeetingCreateSchema, team_id: int) -> MeetingCreateSuccessSchema:
        """
        Creates a new meeting for a team.

        Args:
            meeting_data (MeetingCreateSchema): Data required to create the meeting.
            team_id (int): ID of the team the meeting belongs to.

        Returns:
            MeetingCreateSuccessSchema: Schema containing the ID of the created meeting.

        Raises:
            HTTPException: If a meeting already exists at the given date and time or on database error.
        """
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
        """
        Retrieves all meetings for a specific team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[MeetingSchema]: List of meeting schemas.
        """
        meetings = await self.manager.get_meetings_by_team(team_id)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def get_meetings_by_member(self, member_id: int, team_id: int) -> list[MeetingSchema]:
        """
        Retrieves all meetings for a specific member within a team.

        Args:
            member_id (int): ID of the member.
            team_id (int): ID of the team.

        Returns:
            list[MeetingSchema]: List of meeting schemas.
        """
        meetings = await self.manager.get_meetings_by_member(member_id, team_id)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def update_meeting(
        self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int
    ) -> MeetingUpdateSuccessSchema:
        """
        Updates an existing meeting.

        Args:
            meeting_data (MeetingUpdateSchema): Data to update the meeting.
            meeting_id (int): ID of the meeting to update.
            team_id (int): ID of the team the meeting belongs to.

        Returns:
            MeetingUpdateSuccessSchema: Success schema for the update.

        Raises:
            HTTPException: If the meeting does not exist, overlaps with another, or on database error.
        """
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
        """
        Deletes a meeting by its ID.

        Args:
            meeting_id (int): ID of the meeting to delete.

        Raises:
            HTTPException: If the meeting does not exist.
        """
        deleted = await self.manager.delete_meeting(meeting_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The meeting was not found',
            )


def get_meeting_service(manager: Annotated[MeetingManager, Depends(get_meeting_manager)]) -> MeetingService:
    """
    Dependency injector for MeetingService.

    Args:
        manager (MeetingManager): Injected MeetingManager instance.

    Returns:
        MeetingService: Initialized MeetingService instance.
    """
    return MeetingService(manager=manager)
