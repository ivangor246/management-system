import datetime

from .base import BaseSchema
from .meetings import MeetingSchema
from .tasks import TaskSchema


class CalendarDateSchema(BaseSchema):
    date: datetime.date
    events: list[TaskSchema | MeetingSchema]


class CalendarMonthSchema(BaseSchema):
    year: int
    month: int
    events: list[TaskSchema | MeetingSchema]
