from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.meetings import Meeting
from app.models.users import User
from app.schemas.meetings import MeetingCreateSchema, MeetingUpdateSchema


class MeetingManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __check_meeting(self, meeting_data: MeetingCreateSchema, team_id: int) -> bool:
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

    async def create_meeting(self, meeting_data: MeetingCreateSchema, team_id: int) -> Meeting:
        existing_meeting = await self.__check_meeting(meeting_data, team_id)
        if existing_meeting:
            raise ValueError('A meeting already exists at the given date and time')

        new_meeting = Meeting(
            name=meeting_data.name,
            date=meeting_data.date,
            time=meeting_data.time,
            team_id=team_id,
        )

        if meeting_data.member_ids:
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
        stmt = select(Meeting).where(Meeting.team_id == team_id).options(selectinload(Meeting.users))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_meetings_by_member(self, member_id: int, team_id: int) -> list[Meeting]:
        stmt = (
            select(Meeting)
            .join(Meeting.users)
            .where(User.id == member_id, Meeting.team_id == team_id)
            .options(selectinload(Meeting.users))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_meeting(self, meeting_data: MeetingUpdateSchema, meeting_id: int, team_id: int) -> Meeting | None:
        existing_meeting = self.__check_meeting(meeting_data, team_id)
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
            stmt = select(User).where(User.id.in_(meeting_data.member_ids))
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            meeting.users.extend(users)

        try:
            await self.session.commit()
            await self.session.refresh(meeting)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return meeting

    async def delete_meeting(self, meeting_id: int) -> bool:
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
    return MeetingManager(session=session)
