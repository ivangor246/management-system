from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, str_100

if TYPE_CHECKING:
    from .users import User


class UserRoles(str, Enum):
    USER = 'u'
    MANAGER = 'm'
    ADMIN = 'a'


class Team(Base):
    __tablename__ = 'teams'

    name: Mapped[str_100]

    members: Mapped[list['UserTeam']] = relationship(back_populates='team')


class UserTeam(Base):
    __tablename__ = 'user_team_association'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    role: Mapped['UserRoles'] = mapped_column(
        SQLEnum(UserRoles, name='user_role_enum', native_enum=True),
        default=UserRoles.USER,
    )

    user: Mapped['User'] = relationship(back_populates='teams')
    team: Mapped['Team'] = relationship(back_populates='members')
