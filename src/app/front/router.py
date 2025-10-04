from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_member
from app.schemas.tasks import TaskStatuses
from app.schemas.teams import UserRoles
from app.services.calendar import CalendarService, get_calendar_service
from app.services.tasks import TaskService, get_task_service
from app.services.teams import TeamService, get_team_service

from .utils import get_context

templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter(dependencies=[Depends(get_context)])


@front_router.get('/', response_class=HTMLResponse)
async def home_page(
    request: Request,
    team_service: Annotated[TeamService, Depends(get_team_service)],
):
    context = request.state.context
    teams = []
    user = context.get('user')
    if user:
        teams = await team_service.get_teams_by_user(user.id)
        for team in teams:
            if team.role == UserRoles.ADMIN:
                team.role = 'Админ'
            elif team.role == UserRoles.MANAGER:
                team.role = 'Менеджер'
            else:
                team.role = 'Пользователь'
        context['teams'] = teams

    return templates.TemplateResponse('home.html', {'request': request, 'context': context})


@front_router.get('/teams/{team_id:int}', response_class=HTMLResponse)
async def team_page(
    team_id: int,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    team_service: Annotated[TeamService, Depends(get_team_service)],
    calendar_service: Annotated[CalendarService, Depends(get_calendar_service)],
):
    context = request.state.context
    context['team_id'] = team_id
    user = context.get('user')
    if user:
        try:
            await require_member(team_id, user, session)

            tasks = await task_service.get_tasks_by_team(team_id)
            for task in tasks:
                if task.status == TaskStatuses.OPEN:
                    task.status = 'Открыта'
                elif task.status == TaskStatuses.WORK:
                    task.status = 'В работе'
                else:
                    task.status = 'Завершена'
            context['tasks'] = tasks

            users = await team_service.get_users(team_id)
            for user in users:
                if user.role == UserRoles.ADMIN:
                    user.role = 'Админ'
                elif user.role == UserRoles.MANAGER:
                    user.role = 'Менеджер'
                else:
                    user.role = 'Пользователь'
            context['users'] = users

            context['evaluation'] = await team_service.get_avg_evaluation(user.user_id, team_id)

            now = datetime.now()
            context['calendar_day'] = await calendar_service.get_calendar_by_date(team_id, now.date())
            context['calendar_month'] = await calendar_service.get_calendar_by_month(team_id, now.year, now.month)
        except HTTPException:
            ...

    return templates.TemplateResponse('team.html', {'request': request, 'context': context})


@front_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    context = request.state.context
    return templates.TemplateResponse('register.html', {'request': request, 'context': context})


@front_router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    context = request.state.context
    return templates.TemplateResponse('login.html', {'request': request, 'context': context})


@front_router.get('/profile', response_class=HTMLResponse)
async def profile_page(request: Request):
    context = request.state.context
    return templates.TemplateResponse('profile.html', {'request': request, 'context': context})
