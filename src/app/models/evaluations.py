from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .tasks import Task
    from .users import User


class Evaluation(Base):
    __tablename__ = 'evaluations'

    value: Mapped[int]
    evaluator_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'))

    evaluator: Mapped['User'] = relationship(back_populates='evaluations')
    task: Mapped['Task'] = relationship(back_populates='evaluations')

    __table_args__ = (CheckConstraint('value BETWEEN 1 AND 5', name='check_value_between_1_5'),)
