import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_user
from app.models.users import User
from app.schemas.calendar import CalendarDateSchema, CalendarMonthSchema
from app.services.calendar import CalendarService, get_calendar_service

calendar_router = APIRouter(prefix='/{team_id:int}/calendar', tags=['calendar'])


@calendar_router.get('/date')
async def get_calendar_by_date(
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    date: datetime.date,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> CalendarDateSchema:
    """
    Retrieve all events (tasks and meetings) for a specific team on a given date.

    Args:
        service (CalendarService): Calendar service dependency.
        date (datetime.date): The target date to fetch events.
        team_id (int): ID of the team to query events for.
        member (User): Authenticated user performing the request.

    Returns:
        CalendarDateSchema: A list of events occurring on the specified date.
    """
    return await service.get_calendar_by_date(team_id, date)


@calendar_router.get('/month')
async def get_calendar_by_month(
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    year: int,
    month: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> CalendarMonthSchema:
    """
    Retrieve all events (tasks and meetings) for a specific team within a given month.

    Args:
        service (CalendarService): Calendar service dependency.
        year (int): Year of the month to fetch events for.
        month (int): Month (1-12) to fetch events for.
        team_id (int): ID of the team to query events for.
        member (User): Authenticated user performing the request.

    Returns:
        CalendarMonthSchema: A list of events occurring within the specified month.
    """
    return await service.get_calendar_by_month(team_id, year, month)
