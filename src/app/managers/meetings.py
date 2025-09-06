from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.meetings import Meeting
from app.models.teams import UserTeam
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema, MeetingUpdateSchema


class MeetingManager:
    """Manager class for handling meeting-related operations.

    This class provides methods for creating, retrieving, updating, and deleting
    meetings within a team. It also manages meeting participants.

    Attributes:
        session (AsyncSession): SQLAlchemy asynchronous session for database operations.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the MeetingManager with a database session.

        Args:
            session (AsyncSession): Async SQLAlchemy session.
        """
        self.session = session

    async def __check_is_meeting_exists(self, meeting_data: MeetingCreateSchema, team_id: int) -> bool:
        """Check if a meeting already exists for a given date, time, and team.

        Args:
            meeting_data (MeetingCreateSchema): Meeting creation data.
            team_id (int): ID of the team.

        Returns:
            bool: True if a meeting already exists, otherwise False.
        """
        stmt = select(Meeting).where(
            Meeting.team_id == team_id,
            Meeting.date == meeting_data.date,
            Meeting.time == meeting_data.time,
        )
        result = await self.session.execute(stmt)
        existing_meeting = result.scalar_one_or_none()
        if existing_meeting:
            return True
        return False

    async def __check_meeting_in_team(self, meeting_id: int, team_id: int):
        """
        Check whether a meeting exists and belongs to the given team.

        Args:
            meeting_id (int): ID of the meeting to check.
            team_id (int): ID of the team to validate against.

        Raises:
            LookupError: If the meeting is not found.
            PermissionError: If the meeting does not belong to the given team.
        """
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.session.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise LookupError('The meeting not found')

        if meeting.team_id != team_id:
            raise PermissionError('The meeting does not belong to the team')

    async def __check_user_in_team(self, user_id: int, team_id: int):
        """
        Check whether a task exists and belongs to the given team.

        Args:
            user_id (int): ID of the user to check.
            team_id (int): ID of the team to validate against.

        Raises:
            LookupError: If the user is not found.
        """
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise LookupError('The user not found in this team')

    async def create_meeting(self, meeting_data: MeetingCreateSchema | MeetingUpdateSchema, team_id: int) -> Meeting:
        """Create a new meeting for a team.

        Args:
            meeting_data (MeetingCreateSchema): Meeting creation data.
            team_id (int): ID of the team.

        Raises:
            ValueError: If a meeting already exists at the given date and time.
            SQLAlchemyError: If database commit fails.

        Returns:
            Meeting: The created meeting object.
        """
        existing_meeting = await self.__check_is_meeting_exists(meeting_data, team_id)
        if existing_meeting:
            raise ValueError('A meeting already exists at the given date and time')

        new_meeting = Meeting(
            name=meeting_data.name,
            date=meeting_data.date,
            time=meeting_data.time,
            team_id=team_id,
        )

        if meeting_data.member_ids:
            for member_id in meeting_data.member_ids:
                self.__check_user_in_team(member_id, team_id)

            stmt = select(User).where(User.id.in_(meeting_data.member_ids))
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            new_meeting.users.extend(users)

        self.session.add(new_meeting)

        try:
            await self.session.commit()
            await self.session.refresh(new_meeting)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return new_meeting

    async def get_meetings_by_team(self, team_id: int) -> list[Meeting]:
        """Retrieve all meetings for a given team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[Meeting]: List of meetings with participants loaded.
        """
        stmt = select(Meeting).where(Meeting.team_id == team_id).options(selectinload(Meeting.users))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_meetings_by_member(self, member_id: int, team_id: int) -> list[Meeting]:
        """Retrieve all meetings in which a specific member participates within a team.

        Args:
            member_id (int): ID of the member (user).
            team_id (int): ID of the team.

        Returns:
            list[Meeting]: List of meetings with participants loaded.
        """
        stmt = (
            select(Meeting)
            .join(Meeting.users)
            .where(User.id == member_id, Meeting.team_id == team_id)
            .options(selectinload(Meeting.users))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_meeting(self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int) -> Meeting | None:
        """Update details of an existing meeting.

        Args:
            meeting_data (MeetingUpdateSchema): Data to update the meeting.
            meeting_id (int): ID of the meeting to update.
            team_id (int): ID of the team.

        Raises:
            ValueError: If a meeting already exists at the new date and time.
            SQLAlchemyError: If database commit fails.

        Returns:
            Meeting | None: The updated meeting object, or None if not found.
        """
        self.__check_meeting_in_team(meeting_id, team_id)

        existing_meeting = await self.__check_is_meeting_exists(meeting_data, team_id)
        if existing_meeting:
            raise ValueError('A meeting already exists at the given date and time')

        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.session.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            return None

        if meeting_data.name is not None:
            meeting.name = meeting_data.name
        if meeting_data.date is not None:
            meeting.date = meeting_data.date
        if meeting_data.time is not None:
            meeting.time = meeting_data.time
        if meeting_data.member_ids is not None:
            for member_id in meeting_data.member_ids:
                self.__check_user_in_team(member_id, team_id)
            stmt = select(User).where(User.id.in_(meeting_data.member_ids))
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            meeting.users = users

        try:
            await self.session.commit()
            await self.session.refresh(meeting)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return meeting

    async def delete_meeting(self, meeting_id: int, team_id: int) -> bool:
        """Delete a meeting by its ID.

        Args:
            meeting_id (int): ID of the meeting.

        Raises:
            SQLAlchemyError: If database commit fails.

        Returns:
            bool: True if the meeting was deleted, False if not found.
        """
        self.__check_meeting_in_team(meeting_id, team_id)

        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.session.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            return False

        await self.session.delete(meeting)
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True


def get_meeting_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> MeetingManager:
    """Dependency provider for MeetingManager.

    Args:
        session (AsyncSession): Async SQLAlchemy session.

    Returns:
        MeetingManager: Instance of MeetingManager.
    """
    return MeetingManager(session=session)
