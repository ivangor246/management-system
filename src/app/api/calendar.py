import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_member
from app.models.users import User
from app.schemas.calendar import CalendarDateSchema, CalendarMonthSchema
from app.services.calendar import CalendarService, get_calendar_service

calendar_router = APIRouter(prefix='/{team_id:int}/calendar', tags=['calendar'])


@calendar_router.get('/date')
async def get_calendar_by_date(
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    date: datetime.date,
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> CalendarDateSchema:
    """
    Retrieve all events (tasks and meetings) for a specific team on a given date.

    Args:
        service (CalendarService): Dependency providing calendar operations.
        date (datetime.date): The date to retrieve events for.
        team_id (int): ID of the team.
        member (User): Authenticated team member performing the request.

    Returns:
        CalendarDateSchema: Schema containing the date and list of events for that date.
    """
    return await service.get_calendar_by_date(team_id, date)


@calendar_router.get('/month')
async def get_calendar_by_month(
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    year: int,
    month: int,
    team_id: int,
    member: Annotated[User, Depends(require_member)],
) -> CalendarMonthSchema:
    """
    Retrieve all events (tasks and meetings) for a specific team within a given month.

    Args:
        service (CalendarService): Dependency providing calendar operations.
        year (int): Year of the target month.
        month (int): Month number (1-12).
        team_id (int): ID of the team.
        member (User): Authenticated team member performing the request.

    Returns:
        CalendarMonthSchema: Schema containing year, month, and list of events for that month.
    """
    return await service.get_calendar_by_month(team_id, year, month)
