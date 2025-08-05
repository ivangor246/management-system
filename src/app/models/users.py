from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, str_100

if TYPE_CHECKING:
    from .teams import UserTeam


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(str_100)
    hashed_password: Mapped[str]
    first_name: Mapped[str] = mapped_column(str_100)
    last_name: Mapped[str | None] = mapped_column(str_100)

    teams: Mapped[list['UserTeam']] = relationship(back_populates='user')
