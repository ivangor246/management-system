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
    Service layer responsible for handling meeting-related operations,
    including creation, retrieval, updating, and deletion.

    Attributes:
        manager (MeetingManager): Manager responsible for database operations on meetings.

    Methods:
        create_meeting(meeting_data: MeetingCreateSchema, team_id: int) -> MeetingCreateSuccessSchema:
            Creates a new meeting for a specific team.
        get_meetings_by_team(team_id: int) -> list[MeetingSchema]:
            Retrieves all meetings for a specific team.
        get_meetings_by_member(member_id: int, team_id: int) -> list[MeetingSchema]:
            Retrieves all meetings for a specific member within a team.
        update_meeting(meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int) -> MeetingUpdateSuccessSchema:
            Updates an existing meeting. Raises HTTPException if not found.
        delete_meeting(meeting_id: int, team_id: int) -> None:
            Deletes a meeting by ID. Raises HTTPException if not found or access is denied.
    """

    def __init__(self, manager: MeetingManager):
        """
        Initialize the MeetingService with a MeetingManager.

        Args:
            manager (MeetingManager): Manager instance for handling meeting operations.
        """
        self.manager = manager

    async def create_meeting(self, meeting_data: MeetingCreateSchema, team_id: int) -> MeetingCreateSuccessSchema:
        """
        Create a new meeting for a team.

        Args:
            meeting_data (MeetingCreateSchema): Data required to create the meeting.
            team_id (int): ID of the team the meeting belongs to.

        Returns:
            MeetingCreateSuccessSchema: Schema containing the ID of the created meeting.

        Raises:
            HTTPException: If there is an error during meeting creation.
        """
        try:
            new_meeting = await self.manager.create_meeting(meeting_data, team_id)
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
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

    async def get_meetings_by_team(self, team_id: int, limit: int = 0, offset: int = 0) -> list[MeetingSchema]:
        """
        Retrieve all meetings for a specific team.

        Args:
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of meetings to retrieve. Defaults to 0 (no limit).
            offset (int, optional): Number of meetings to skip before returning results. Defaults to 0.

        Returns:
            list[MeetingSchema]: List of meeting schemas for the specified team.
        """
        meetings = await self.manager.get_meetings_by_team(team_id, limit, offset)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def get_meetings_by_member(
        self, member_id: int, team_id: int, limit: int = 0, offset: int = 0
    ) -> list[MeetingSchema]:
        """
        Retrieve all meetings for a specific member within a team.

        Args:
            member_id (int): ID of the member.
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of meetings to retrieve. Defaults to 0 (no limit).
            offset (int, optional): Number of meetings to skip before returning results. Defaults to 0.

        Returns:
            list[MeetingSchema]: List of meeting schemas for the specified member and team.
        """
        meetings = await self.manager.get_meetings_by_member(member_id, team_id, limit, offset)
        return [MeetingSchema.model_validate(meeting) for meeting in meetings]

    async def update_meeting(
        self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int
    ) -> MeetingUpdateSuccessSchema:
        """
        Update an existing meeting.

        Args:
            meeting_data (MeetingUpdateSchema): Data to update the meeting.
            meeting_id (int): ID of the meeting to update.
            team_id (int): ID of the team the meeting belongs to.

        Returns:
            MeetingUpdateSuccessSchema: Success schema indicating the meeting was updated.

        Raises:
            HTTPException: If the meeting does not exist, access is denied, or an error occurs.
        """
        try:
            meeting = await self.manager.update_meeting(meeting_data, meeting_id, team_id)
            if not meeting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='The meeting was not found',
                )
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{e}',
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

    async def delete_meeting(self, meeting_id: int, team_id: int) -> None:
        """
        Delete a meeting by its ID.

        Args:
            meeting_id (int): ID of the meeting to delete.
            team_id (int): ID of the team the meeting belongs to.

        Raises:
            HTTPException: If the meeting does not exist or access is denied.
        """
        try:
            deleted = await self.manager.delete_meeting(meeting_id, team_id)
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{e}',
            )
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
