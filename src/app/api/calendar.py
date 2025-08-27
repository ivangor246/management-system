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
    return await service.get_calendar_by_date(team_id, date)


@calendar_router.get('/month')
async def get_calendar_by_month(
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    year: int,
    month: int,
    team_id: int,
    member: Annotated[User, Depends(require_user)],
) -> CalendarMonthSchema:
    return await service.get_calendar_by_month(team_id, year, month)
