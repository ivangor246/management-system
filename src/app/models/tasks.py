from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .comments import Comment

if TYPE_CHECKING:
    from .teams import Team
    from .users import User


class TaskStatuses(str, Enum):
    OPEN = 'o'
    WORK = 'w'
    COMPLETED = 'c'


class Task(Base):
    __tablename__ = 'tasks'

    description: Mapped[str]
    deadline: Mapped[date]
    status: Mapped['TaskStatuses'] = mapped_column(
        SQLEnum(TaskStatuses, name='task_status_enum', native_enum=True),
        default=TaskStatuses.OPEN,
    )
    performer_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'))
    score: Mapped[int | None] = mapped_column(default=None)

    performer: Mapped[Optional['User']] = relationship(back_populates='tasks')
    team: Mapped['Team'] = relationship(back_populates='tasks')
    comments: Mapped[list['Comment']] = relationship(back_populates='task')

    __table_args__ = (CheckConstraint('score BETWEEN 1 AND 5', name='check_score_between_1_5'),)
