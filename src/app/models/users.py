from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, str_100
from .comments import Comment
from .tasks import Task
from .teams import UserTeam


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str_100] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str_100]
    first_name: Mapped[str_100]
    last_name: Mapped[str_100 | None]
    is_admin: Mapped[bool] = mapped_column(default=False)

    teams: Mapped[list['UserTeam']] = relationship(back_populates='user')
    tasks: Mapped[list['Task']] = relationship(back_populates='performer')
    comments: Mapped[list['Comment']] = relationship(back_populates='user')
