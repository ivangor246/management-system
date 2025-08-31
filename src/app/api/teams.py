from datetime import date
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

from .calendar import calendar_router
from .meetings import meetings_router
from .tasks import tasks_router

teams_router = APIRouter(prefix='/teams', tags=['teams'])


@teams_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_team(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_data: TeamCreateSchema,
    auth_user: Annotated[User, Depends(get_request_user)],
) -> TeamCreateSuccessSchema:
    """
    Create a new team.

    Args:
        service (TeamService): Team service dependency.
        team_data (TeamCreateSchema): Data for the new team.
        auth_user (User): User creating the team.

    Returns:
        TeamCreateSuccessSchema: ID of the newly created team.
    """
    return await service.create_team(team_data, auth_user)


@teams_router.get('/')
async def get_my_teams(
    service: Annotated[TeamService, Depends(get_team_service)],
    auth_user: Annotated[User, Depends(get_request_user)],
) -> list[TeamByMemberSchema]:
    """
    Retrieve all teams the current user belongs to.

    Args:
        service (TeamService): Team service dependency.
        auth_user (User): Current authenticated user.

    Returns:
        list[TeamByMemberSchema]: List of teams and user's roles.
    """
    return await service.get_teams_by_user(auth_user.id)


@teams_router.get('/{team_id:int}')
async def get_team_members(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> list[TeamMemberSchema]:
    """
    Retrieve all members of a specific team.

    Args:
        service (TeamService): Team service dependency.
        team_id (int): ID of the team.
        member (User): User requesting team members.

    Returns:
        list[TeamMemberSchema]: List of team members and their roles.
    """
    return await service.get_users(team_id)


@teams_router.get('/{team_id:int}/avg-score')
async def get_avg_score(
    service: Annotated[TeamService, Depends(get_team_service)],
    start_date: date,
    end_date: date,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> float:
    """
    Retrieve the average score of a user in a team within a date range.

    Args:
        service (TeamService): Team service dependency.
        start_date (date): Start date of the range.
        end_date (date): End date of the range.
        team_id (int): ID of the team.
        member (User): User requesting the average score.

    Returns:
        float: Average score of the user.
    """
    return await service.get_avg_score(member.id, team_id, start_date, end_date)


@teams_router.post('/{team_id:int}/users')
async def add_team_member(
    service: Annotated[TeamService, Depends(get_team_service)],
    team_id: int,
    user_team_data: UserTeamCreateSchema,
    manager: Annotated[User, Depends(require_manager)],
) -> UserTeamCreateSuccessSchema:
    """
    Add a user to a team with a specified role.

    Args:
        service (TeamService): Team service dependency.
        team_id (int): ID of the team.
        user_team_data (UserTeamCreateSchema): Data of the user and role to add.
        manager (User): Manager adding the user to the team.

    Returns:
        UserTeamCreateSuccessSchema: Success response for the user-team association.
    """
    return await service.create_user_team_association(user_team_data, team_id)


@teams_router.delete('/{team_id:int}/users/{user_id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    service: Annotated[TeamService, Depends(get_team_service)],
    user_id: int,
    team_id: int,
    manager: Annotated[User, Depends(require_manager)],
):
    """
    Remove a user from a team.

    Args:
        service (TeamService): Team service dependency.
        user_id (int): ID of the user to remove.
        team_id (int): ID of the team.
        manager (User): Manager performing the removal.

    Returns:
        None
    """
    await service.remove_user_from_team(user_id, team_id)


teams_router.include_router(tasks_router)
teams_router.include_router(meetings_router)
teams_router.include_router(calendar_router)
