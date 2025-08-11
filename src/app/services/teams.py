from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.managers.teams import TeamManager, get_team_manager
from app.models.users import User
from app.schemas.teams import TeamCreateSchema, TeamCreateSuccessSchema


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


def get_team_service(manager: Annotated[TeamManager, Depends(get_team_manager)]) -> TeamService:
    return TeamService(manager=manager)
