from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.evaluations import Evaluation
from app.models.tasks import Task
from app.models.teams import Team, UserTeam
from app.models.users import User
from app.schemas.teams import TeamCreateSchema, UserRoles


class TeamManager:
    """
    Manager class for handling operations related to Teams, Users, and their associations.

    This class provides methods to create teams, assign user roles,
    fetch users by team, fetch teams by user, calculate average evaluations,
    and manage team-user associations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the TeamManager with a given database session.

        Args:
            session (AsyncSession): The SQLAlchemy asynchronous session.
        """
        self.session = session

    async def create_team(self, team_data: TeamCreateSchema, user_to_admin: User) -> Team:
        """
        Create a new team and assign the given user as an admin.

        Args:
            team_data (TeamCreateSchema): Data for creating a new team.
            user_to_admin (User): User who will be assigned as the team admin.

        Returns:
            Team: The newly created team instance.
        """
        new_team = Team(name=team_data.name)
        self.session.add(new_team)

        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        await self.session.refresh(new_team)

        await self.assign_role(user_id=user_to_admin.id, team_id=new_team.id, role=UserRoles.ADMIN)

        return new_team

    async def assign_role(self, user_id: int, team_id: int, role: UserRoles) -> UserTeam:
        """
        Assign a role to a user in a team. If the association already exists,
        the role will be updated.

        Args:
            user_id (int): ID of the user.
            team_id (int): ID of the team.
            role (UserRoles): Role to assign.

        Returns:
            UserTeam: The updated or newly created user-team association.
        """
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
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return new_user_team_association

    async def get_users(self, team_id: int) -> list[tuple[User, UserRoles]]:
        """
        Get all users and their roles in a specific team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[tuple[User, UserRoles]]: List of users with their assigned roles.
        """
        stmt = (
            select(User, UserTeam.role)
            .join(
                UserTeam,
                UserTeam.user_id == User.id,
            )
            .where(UserTeam.team_id == team_id)
        )
        result = await self.session.execute(stmt)
        return [(user, role) for user, role in result.all()]

    async def get_teams_by_user(self, user_id: int) -> list[tuple[Team, UserRoles]]:
        """
        Get all teams that a specific user belongs to along with their roles.

        Args:
            user_id (int): ID of the user.

        Returns:
            list[tuple[Team, UserRoles]]: List of teams with the user's role in each.
        """
        stmt = (
            select(Team, UserTeam.role)
            .join(
                UserTeam,
                UserTeam.team_id == Team.id,
            )
            .where(UserTeam.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return [(team, role) for team, role in result.all()]

    async def delete_user_team_association(self, user_id: int, team_id: int) -> bool:
        """
        Remove a user's association with a team.
        If no associations remain for the team, delete the team as well.

        Args:
            user_id (int): ID of the user.
            team_id (int): ID of the team.

        Returns:
            bool: True if the association was deleted, False if not found.
        """
        stmt = select(UserTeam).where(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
        result = await self.session.execute(stmt)
        association = result.scalar_one_or_none()

        if not association:
            return False

        await self.session.delete(association)
        await self.session.flush()

        check_stmt = select(UserTeam).where(UserTeam.team_id == team_id)
        remaining = await self.session.execute(check_stmt)
        if not remaining.first():
            team_stmt = select(Team).where(Team.id == team_id)
            team_result = await self.session.execute(team_stmt)
            team = team_result.scalar_one_or_none()
            if team:
                await self.session.delete(team)
                await self.session.flush()

        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True

    async def get_avg_evaluation(self, user_id: int, team_id: int) -> float:
        """
        Calculate the average evaluation of tasks performed by a user in a specific team
        within a date range.

        Args:
            user_id (int): ID of the user.
            team_id (int): ID of the team.

        Returns:
            float: The average evaluation rounded to 2 decimal places, or 0.0 if no evaluation exists.
        """
        stmt = (
            select(func.avg(Evaluation.value))
            .join(Task, Task.id == Evaluation.task_id)
            .where(
                Task.performer_id == user_id,
                Task.team_id == team_id,
            )
        )
        result = await self.session.execute(stmt)
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg is not None else 0.0


def get_team_manager(session: Annotated[AsyncSession, Depends(get_session)]) -> TeamManager:
    """
    Dependency function to provide a TeamManager instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        TeamManager: An instance of TeamManager.
    """
    return TeamManager(session=session)
