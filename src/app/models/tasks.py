from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .comments import Comment

if TYPE_CHECKING:
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

    performer: Mapped[Optional['User']] = relationship(back_populates='tasks')
    comments: Mapped[list['Comment']] = relationship(back_populates='task')
