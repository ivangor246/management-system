import datetime
from typing import Annotated

from fastapi import Depends

from app.managers.meetings import MeetingManager, get_meeting_manager
from app.managers.tasks import TaskManager, get_task_manager
from app.schemas.calendar import CalendarDateSchema, CalendarMonthSchema
from app.schemas.meetings import MeetingSchema
from app.schemas.tasks import TaskSchema


class CalendarService:
    """
    Service for retrieving calendar events (tasks and meetings) for a team.
    """

    def __init__(self, task_manager: TaskManager, meeting_manager: MeetingManager):
        """
        Initialize CalendarService with task and meeting managers.

        Args:
            task_manager (TaskManager): Manager responsible for task operations.
            meeting_manager (MeetingManager): Manager responsible for meeting operations.
        """
        self.task_manager = task_manager
        self.meeting_manager = meeting_manager

    async def get_calendar_by_date(self, team_id: int, date: datetime.date) -> CalendarDateSchema:
        """
        Retrieve all tasks and meetings for a team on a specific date.

        Args:
            team_id (int): ID of the team.
            date (datetime.date): Target date to fetch events for.

        Returns:
            CalendarDateSchema: Schema containing the date and the list of events.
        """
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
        """
        Retrieve all tasks and meetings for a team within a specific month.

        Args:
            team_id (int): ID of the team.
            year (int): Target year.
            month (int): Target month (1–12).

        Returns:
            CalendarMonthSchema: Schema containing year, month, and the list of events.
        """
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
    """
    Dependency provider for CalendarService.

    Args:
        task_manager (TaskManager): Injected TaskManager instance.
        meeting_manager (MeetingManager): Injected MeetingManager instance.

    Returns:
        CalendarService: Initialized CalendarService instance.
    """
    return CalendarService(task_manager=task_manager, meeting_manager=meeting_manager)
