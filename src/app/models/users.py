from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, str_100

if TYPE_CHECKING:
    from .teams import UserTeam


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str_100] = mapped_column(unique=True)
    email: Mapped[str]
    hashed_password: Mapped[str_100]
    first_name: Mapped[str_100]
    last_name: Mapped[str_100 | None]

    teams: Mapped[list['UserTeam']] = relationship(back_populates='user')
