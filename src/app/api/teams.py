from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user, require_manager, require_user
from app.models.users import User
from app.schemas.teams import (
    TeamByMemberSchema,
    TeamCreateSchema,
    TeamCreateSuccessSchema,
    TeamMemberSchema,
    UserTeamCreateSchema,
    UserTeamCreateSuccessSchema,
)
from app.services.teams import TeamService, get_team_service

teams_router = APIRouter(prefix='/teams', tags=['teams'])


@teams_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_team(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_data: TeamCreateSchema,
    auth_user: Annotated[User, Depends(get_request_user)],
) -> TeamCreateSuccessSchema:
    return await service.create_team(team_data, auth_user)


@teams_router.get('/{team_id:int}')
async def get_users(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_id: int,
    team_member: Annotated[User, Depends(require_user)],
) -> list[TeamMemberSchema]:
    return await service.get_users(team_id)


@teams_router.get('/my')
async def get_teams_by_user(
    service: Annotated[TeamService, Depends(get_team_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
) -> list[TeamByMemberSchema]:
    return await service.get_teams_by_user(auth_user.id)


@teams_router.post('/{team_id:int}/add')
async def create_user_team_association(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_id: int,
    user_team_data: UserTeamCreateSchema,
    team_manager: Annotated[User, Depends(require_manager)],
) -> UserTeamCreateSuccessSchema:
    return await service.create_user_team_association(user_team_data, team_id)
