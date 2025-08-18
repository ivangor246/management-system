from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.tasks import Task
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
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        existing_association = await self.session.scalar(stmt)

        if existing_association:
            existing_association.role = role
            new_user_team_association = existing_association
        else:
            new_user_team_association = UserTeam(
                user_id=user_id,
                team_id=team_id,
                role=role,
            )
            self.session.add(new_user_team_association)

        try:
            await self.session.commit()
            await self.session.refresh(new_user_team_association)
        except:
            await self.session.rollback()
            raise

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

    async def delete_user_team_association(self, user_id: int, team_id: int) -> bool:
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        result = await self.session.execute(stmt)
        association = result.scalar_one_or_none()

        if not association:
            return False

        await self.session.delete(association)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return True

    async def get_avg_score(self, user_id: int, team_id: int, start_date: date, end_date: date) -> float:
        stmt = select(func.avg(Task.score)).where(
            Task.performer_id == user_id,
            Task.team_id == team_id,
            Task.score.isnot(None),
            Task.created_at >= start_date,
            Task.created_at <= end_date,
        )
        result = await self.session.execute(stmt)
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg is not None else 0.0


def get_team_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TeamManager:
    return TeamManager(session=session)
