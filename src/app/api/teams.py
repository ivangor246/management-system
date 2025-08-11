from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_request_user
from app.models.users import User
from app.schemas.teams import TeamCreateSchema, TeamCreateSuccessSchema
from app.services.teams import TeamService, get_team_service

teams_router = APIRouter(prefix='/teams', tags=['teams'])


@teams_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_team(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_data: TeamCreateSchema,
    user: Annotated[User, Depends(get_request_user)],
) -> TeamCreateSuccessSchema:
    return await service.create_team(team_data, user)
