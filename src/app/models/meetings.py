from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, str_100

if TYPE_CHECKING:
    from .teams import Team
    from .users import User

user_meeting_association = Table(
    'user_meeting',
    Base.metadata,
    Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('meeting_id', ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True),
)


class Meeting(Base):
    __tablename__ = 'meetings'

    name: Mapped[str_100]
    date: Mapped[date]
    time: Mapped[time]
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'))

    users: Mapped[list['User']] = relationship(
        'User',
        secondary=user_meeting_association,
        back_populates='meetings',
        lazy='selectin',
    )
    team: Mapped['Team'] = relationship(back_populates='meetings')
