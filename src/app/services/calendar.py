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
    Service to retrieve calendar events (tasks and meetings) for a team.

    Attributes:
        task_manager (TaskManager): Manager responsible for task operations.
        meeting_manager (MeetingManager): Manager responsible for meeting operations.

    Methods:
        get_calendar_by_date(team_id: int, date: datetime.date) -> CalendarDateSchema:
            Returns all tasks and meetings for a team on a specific date.
        get_calendar_by_month(team_id: int, year: int, month: int) -> CalendarMonthSchema:
            Returns all tasks and meetings for a team in a specific month.
    """

    def __init__(self, task_manager: TaskManager, meeting_manager: MeetingManager):
        """
        Initializes the CalendarService with task and meeting managers.

        Args:
            task_manager (TaskManager): Task manager instance.
            meeting_manager (MeetingManager): Meeting manager instance.
        """
        self.task_manager = task_manager
        self.meeting_manager = meeting_manager

    async def get_calendar_by_date(self, team_id: int, date: datetime.date) -> CalendarDateSchema:
        """
        Retrieves all tasks and meetings for a team on a specific date.

        Args:
            team_id (int): ID of the team.
            date (datetime.date): The target date to fetch events for.

        Returns:
            CalendarDateSchema: Schema containing the date and list of events for that date.
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
        Retrieves all tasks and meetings for a team within a specific month.

        Args:
            team_id (int): ID of the team.
            year (int): Year of the target month.
            month (int): Month number (1-12).

        Returns:
            CalendarMonthSchema: Schema containing year, month, and list of events within that month.
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
    Dependency injector for CalendarService.

    Args:
        task_manager (TaskManager): Injected TaskManager instance.
        meeting_manager (MeetingManager): Injected MeetingManager instance.

    Returns:
        CalendarService: Initialized CalendarService instance.
    """
    return CalendarService(task_manager=task_manager, meeting_manager=meeting_manager)
