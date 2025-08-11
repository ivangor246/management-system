from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.teams import Team, UserTeam
from app.models.users import User
from app.schemas.teams import TeamCreateSchema, UserRoles


class TeamManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_team(self, team_data: TeamCreateSchema, user_to_admin: User) -> Team:
        new_team = Team(name=team_data.name)
        self.session.add(new_team)

        try:
            await self.session.commit()
        except:
            await self.session.rollback()
            raise

        await self.session.refresh(new_team)

        await self.assign_role(user_id=user_to_admin.id, team_id=new_team.id, role=UserRoles.ADMIN)

        return new_team

    async def assign_role(self, user_id: int, team_id: int, role: UserRoles) -> UserTeam:
        new_user_team_association = UserTeam(
            user_id=user_id,
            team_id=team_id,
            role=role,
        )
        self.session.add(new_user_team_association)

        try:
            await self.session.commit()
        except:
            await self.session.rollback()
            raise

        await self.session.refresh(new_user_team_association)
        return new_user_team_association

    async def get_users(self, team_id: int) -> list[tuple[User, UserRoles]]:
        stmt = (
            select(User, UserTeam.role)
            .join(
                UserTeam,
                UserTeam.user_id == User.id,
            )
            .where(UserTeam.team_id == team_id)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_teams_by_user(self, user_id: int) -> list[tuple[Team, UserRoles]]:
        stmt = (
            select(Team, UserTeam.role)
            .join(
                UserTeam,
                UserTeam.team_id == Team.id,
            )
            .where(UserTeam.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.all()


def get_team_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TeamManager:
    return TeamManager(session=session)
