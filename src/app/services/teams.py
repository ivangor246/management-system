from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.teams import TeamManager, get_team_manager
from app.models.users import User
from app.schemas.teams import (
    TeamByMemberSchema,
    TeamCreateSchema,
    TeamCreateSuccessSchema,
    TeamMemberSchema,
    UserTeamCreateSchema,
    UserTeamCreateSuccessSchema,
)


class TeamService:
    """
    Service responsible for managing teams, their members, and related operations.

    Attributes:
        manager (TeamManager): Manager responsible for team database operations.

    Methods:
        create_team(team_data: TeamCreateSchema, user_to_admin: User) -> TeamCreateSuccessSchema:
            Creates a new team and assigns the specified user as an admin.
        get_users(team_id: int) -> list[TeamMemberSchema]:
            Retrieves all users and their roles for a specific team.
        get_teams_by_user(user_id: int) -> list[TeamByMemberSchema]:
            Retrieves all teams a user is part of along with their roles.
        create_user_team_association(user_team_data: UserTeamCreateSchema, team_id: int) -> UserTeamCreateSuccessSchema:
            Assigns a user to a team with a specific role.
        remove_user_from_team(user_id: int, team_id: int) -> None:
            Removes a user from a team.
        get_avg_evaluation(user_id: int, team_id: int, start_date: date, end_date: date) -> float:
            Calculates the average evaluation of a user in a team over a given date range.
    """

    def __init__(self, manager: TeamManager):
        """
        Initializes the TeamService with a TeamManager.

        Args:
            manager (TeamManager): The manager instance for handling team operations.
        """
        self.manager = manager

    async def create_team(self, team_data: TeamCreateSchema, user_to_admin: User) -> TeamCreateSuccessSchema:
        """
        Creates a new team and assigns the specified user as an admin.

        Args:
            team_data (TeamCreateSchema): Data required to create the team.
            user_to_admin (User): User who will be assigned as team admin.

        Returns:
            TeamCreateSuccessSchema: Schema containing the ID of the newly created team.

        Raises:
            HTTPException: If an error occurs during team creation.
        """
        try:
            new_team = await self.manager.create_team(team_data, user_to_admin)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong',
            )
        return TeamCreateSuccessSchema(team_id=new_team.id)

    async def get_users(self, team_id: int) -> list[TeamMemberSchema]:
        """
        Retrieves all users and their roles for a specific team.

        Args:
            team_id (int): ID of the team.

        Returns:
            list[TeamMemberSchema]: List of team members with their roles.

        Raises:
            HTTPException: If the team is not found.
        """
        users_and_roles = await self.manager.get_users(team_id)

        if not users_and_roles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Team not found',
            )

        members = [
            TeamMemberSchema(
                user_id=user.id,
                username=user.username,
                role=role,
            )
            for user, role in users_and_roles
        ]
        return members

    async def get_teams_by_user(self, user_id: int) -> list[TeamByMemberSchema]:
        """
        Retrieves all teams a user is part of along with their roles.

        Args:
            user_id (int): ID of the user.

        Returns:
            list[TeamByMemberSchema]: List of teams with the user's role in each.
        """
        teams_and_roles = await self.manager.get_teams_by_user(user_id)
        teams = [
            TeamByMemberSchema(
                team_id=team.id,
                name=team.name,
                role=role,
            )
            for team, role in teams_and_roles
        ]
        return teams

    async def create_user_team_association(
        self, user_team_data: UserTeamCreateSchema, team_id: int
    ) -> UserTeamCreateSuccessSchema:
        """
        Assigns a user to a team with a specific role.

        Args:
            user_team_data (UserTeamCreateSchema): User ID and role to assign.
            team_id (int): ID of the team.

        Returns:
            UserTeamCreateSuccessSchema: Confirmation of the association.

        Raises:
            HTTPException: If an error occurs while adding the user to the team.
        """
        try:
            await self.manager.assign_role(user_team_data.user_id, team_id, user_team_data.role)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong while adding the user-team association',
            )
        return UserTeamCreateSuccessSchema()

    async def remove_user_from_team(self, user_id: int, team_id: int) -> None:
        """
        Removes a user from a team.

        Args:
            user_id (int): ID of the user to remove.
            team_id (int): ID of the team.

        Raises:
            HTTPException: If the user is not a member of the team.
        """
        deleted = await self.manager.delete_user_team_association(user_id, team_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The user is not a member of this team',
            )

    async def get_avg_evaluation(self, user_id: int, team_id: int) -> float:
        """
        Calculates the average evaluation of a user in a team over a given date range.

        Args:
            user_id (int): ID of the user.
            team_id (int): ID of the team.

        Returns:
            float: Average evaluation, rounded to 2 decimal places.
        """
        return await self.manager.get_avg_evaluation(user_id, team_id)


def get_team_service(manager: Annotated[TeamManager, Depends(get_team_manager)]) -> TeamService:
    """
    Dependency injector for TeamService.

    Args:
        manager (TeamManager): Injected TeamManager instance.

    Returns:
        TeamService: Initialized TeamService instance.
    """
    return TeamService(manager=manager)
