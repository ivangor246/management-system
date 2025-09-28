from datetime import date, datetime, time, timezone
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
    """
    Manager for handling meeting-related operations.

    Provides methods for creating, retrieving, updating, and deleting
    meetings within a team, as well as validating participants.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize MeetingManager.

        Args:
            session (AsyncSession): SQLAlchemy async session for database operations.
        """
        self.session = session

    def __check_ids_is_not_empty(self, ids: list[int]) -> None:
        """
        Ensure that a list of member IDs is not empty.

        Args:
            ids (list[int]): List of user IDs.

        Raises:
            ValueError: If the list is empty.
        """
        if not ids:
            raise ValueError('Meeting must include at least one member')

    def __check_meeting_datetime(self, meeting_date: date, meeting_time: time) -> None:
        """
        Ensure that a meeting date and time are not in the past.

        Args:
            meeting_date (date): Meeting date.
            meeting_time (time): Meeting time.

        Raises:
            ValueError: If the combined datetime is in the past.
        """
        meeting_datetime = datetime.combine(meeting_date, meeting_time, tzinfo=timezone.utc)
        if meeting_datetime < datetime.now(timezone.utc):
            raise ValueError('Meeting date and time cannot be in the past')

    async def __check_is_meeting_exists(
        self, meeting_data: MeetingCreateSchema | MeetingUpdateSchema, team_id: int
    ) -> None:
        """
        Check whether a meeting already exists for a given date, time, and team.

        Args:
            meeting_data (MeetingCreateSchema | MeetingUpdateSchema): Meeting data.
            team_id (int): ID of the team.

        Raises:
            ValueError: If a meeting already exists at the given date and time.
        """
        stmt = select(Meeting).where(
            Meeting.team_id == team_id,
            Meeting.date == meeting_data.date,
            Meeting.time == meeting_data.time,
        )
        result = await self.session.execute(stmt)
        existing_meeting = result.scalar_one_or_none()

        if existing_meeting:
            raise ValueError('A meeting already exists at the given date and time')

    async def __check_meeting_in_team(self, meeting_id: int, team_id: int) -> None:
        """
        Ensure that a meeting exists and belongs to the given team.

        Args:
            meeting_id (int): ID of the meeting.
            team_id (int): ID of the team.

        Raises:
            LookupError: If the meeting is not found.
            PermissionError: If the meeting belongs to another team.
        """
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.session.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise LookupError('Meeting not found')

        if meeting.team_id != team_id:
            raise PermissionError('Meeting does not belong to the given team')

    async def __check_user_in_team(self, user_id: int, team_id: int) -> None:
        """
        Ensure that a user belongs to the given team.

        Args:
            user_id (int): ID of the user.
            team_id (int): ID of the team.

        Raises:
            LookupError: If the user is not found in the team.
        """
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise LookupError('User not found in this team')

    async def create_meeting(self, meeting_data: MeetingCreateSchema | MeetingUpdateSchema, team_id: int) -> Meeting:
        """
        Create a new meeting for a team.

        Args:
            meeting_data (MeetingCreateSchema | MeetingUpdateSchema): Meeting creation data.
            team_id (int): ID of the team.

        Returns:
            Meeting: The created meeting instance.

        Raises:
            ValueError: If `member_ids` is empty, if a meeting already exists at
                        the given date and time, or if the date/time are in the past.
            LookupError: If a specified user is not in the team.
            SQLAlchemyError: If a database error occurs during commit.
        """
        self.__check_ids_is_not_empty(meeting_data.member_ids)
        self.__check_meeting_datetime(meeting_data.date, meeting_data.time)
        await self.__check_is_meeting_exists(meeting_data, team_id)

        new_meeting = Meeting(
            name=meeting_data.name,
            date=meeting_data.date,
            time=meeting_data.time,
            team_id=team_id,
        )

        for member_id in meeting_data.member_ids:
            await self.__check_user_in_team(member_id, team_id)

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

    async def get_meetings_by_team(self, team_id: int, limit: int = 0, offset: int = 0) -> list[Meeting]:
        """
        Retrieve all meetings for a given team.

        Args:
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of meetings to return. Defaults to 0 (no limit).
            offset (int, optional): Number of meetings to skip. Defaults to 0.

        Returns:
            list[Meeting]: List of meetings with participants preloaded.
        """
        stmt = select(Meeting).where(Meeting.team_id == team_id).options(selectinload(Meeting.users))
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_meetings_by_member(
        self, member_id: int, team_id: int, limit: int = 0, offset: int = 0
    ) -> list[Meeting]:
        """
        Retrieve all meetings a specific member participates in within a team.

        Args:
            member_id (int): ID of the user.
            team_id (int): ID of the team.
            limit (int, optional): Maximum number of meetings to return. Defaults to 0 (no limit).
            offset (int, optional): Number of meetings to skip. Defaults to 0.

        Returns:
            list[Meeting]: List of meetings with participants preloaded.
        """
        stmt = (
            select(Meeting)
            .join(Meeting.users)
            .where(User.id == member_id, Meeting.team_id == team_id)
            .options(selectinload(Meeting.users))
        )
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_meeting(self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int) -> Meeting | None:
        """
        Update details of an existing meeting.

        Args:
            meeting_data (MeetingUpdateSchema): Data to update the meeting.
            meeting_id (int): ID of the meeting.
            team_id (int): ID of the team.

        Returns:
            Meeting | None: The updated meeting instance, or None if not found.

        Raises:
            ValueError: If `member_ids` is empty, if a meeting already exists at
                        the given date and time, or if the date/time are in the past.
            LookupError: If the meeting or a user is not found.
            PermissionError: If the meeting belongs to another team.
            SQLAlchemyError: If a database error occurs during commit.
        """
        await self.__check_meeting_in_team(meeting_id, team_id)
        await self.__check_is_meeting_exists(meeting_data, team_id)

        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.session.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            return None

        self.__check_meeting_datetime(meeting_data.date or meeting.date, meeting_data.time or meeting.time)

        if meeting_data.name is not None:
            meeting.name = meeting_data.name
        if meeting_data.date is not None:
            meeting.date = meeting_data.date
        if meeting_data.time is not None:
            meeting.time = meeting_data.time
        if meeting_data.member_ids is not None:
            self.__check_ids_is_not_empty(meeting_data.member_ids)
            for member_id in meeting_data.member_ids:
                await self.__check_user_in_team(member_id, team_id)
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
        """
        Delete a meeting by its ID.

        Args:
            meeting_id (int): ID of the meeting.
            team_id (int): ID of the team.

        Returns:
            bool: True if the meeting was deleted, False otherwise.

        Raises:
            LookupError: If the meeting is not found.
            PermissionError: If the meeting belongs to another team.
            SQLAlchemyError: If a database error occurs during commit.
        """
        await self.__check_meeting_in_team(meeting_id, team_id)

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
    """
    Dependency provider for MeetingManager.

    Args:
        session (AsyncSession): SQLAlchemy async session.

    Returns:
        MeetingManager: An instance of MeetingManager.
    """
    return MeetingManager(session=session)
