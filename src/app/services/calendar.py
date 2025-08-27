import datetime
from typing import Annotated

from fastapi import Depends

from app.managers.meetings import MeetingManager, get_meeting_manager
from app.managers.tasks import TaskManager, get_task_manager
from app.schemas.calendar import CalendarDateSchema, CalendarMonthSchema
from app.schemas.meetings import MeetingSchema
from app.schemas.tasks import TaskSchema


class CalendarService:
    def __init__(self, task_manager: TaskManager, meeting_manager: MeetingManager):
        self.task_manager = task_manager
        self.meeting_manager = meeting_manager

    async def get_calendar_by_date(self, team_id: int, date: datetime.date) -> CalendarDateSchema:
        tasks = await self.task_manager.get_tasks_by_team(team_id)
        meetings = await self.meeting_manager.get_meetings_by_team(team_id)

        events = []
        for task in tasks:
            if task.deadline == date:
                events.append(TaskSchema.model_validate(task))
        for meeting in meetings:
            if meeting.date == date:
                events.append(MeetingSchema.model_validate(meeting))

        return CalendarDateSchema(date=date, events=events)

    async def get_calendar_by_month(self, team_id: int, year: int, month: int) -> CalendarMonthSchema:
        tasks = await self.task_manager.get_tasks_by_team(team_id)
        meetings = await self.meeting_manager.get_meetings_by_team(team_id)

        events = []
        for task in tasks:
            if task.deadline.year == year and task.deadline.month == month:
                events.append(TaskSchema.model_validate(task))
        for meeting in meetings:
            if meeting.date.year == year and meeting.date.month == month:
                events.append(MeetingSchema.model_validate(meeting))

        return CalendarMonthSchema(year=year, month=month, events=events)


def get_calendar_service(
    task_manager: Annotated[TaskManager, Depends(get_task_manager)],
    meeting_manager: Annotated[MeetingManager, Depends(get_meeting_manager)],
) -> CalendarService:
    return CalendarService(task_manager=task_manager, meeting_manager=meeting_manager)
