from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .tasks import Task
    from .users import User


class Comment(Base):
    __tablename__ = 'comments'

    text: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'))

    user: Mapped['User'] = relationship(back_populates='comments')
    task: Mapped['Task'] = relationship(back_populates='comments')
