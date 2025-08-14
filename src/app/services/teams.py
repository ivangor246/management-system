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
    def __init__(self, manager: TeamManager):
        self.manager = manager

    async def create_team(self, team_data: TeamCreateSchema, user_to_admin: User) -> TeamCreateSuccessSchema:
        try:
            new_team = await self.manager.create_team(team_data, user_to_admin)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong',
            )
        return TeamCreateSuccessSchema(team_id=new_team.id)

    async def get_users(self, team_id: int) -> list[TeamMemberSchema]:
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
        try:
            await self.manager.assign_role(user_team_data.user_id, team_id, user_team_data.role)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Something went wrong while adding the user-team association',
            )
        return UserTeamCreateSuccessSchema()

    async def remove_user_from_team(self, user_id: int, team_id: int) -> None:
        deleted = await self.manager.delete_user_team_association(user_id, team_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The user is not a member of this team',
            )


def get_team_service(manager: Annotated[TeamManager, Depends(get_team_manager)]) -> TeamService:
    return TeamService(manager=manager)
