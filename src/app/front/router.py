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

from .utils import get_context, get_team_role

templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter(dependencies=[Depends(get_context)])


convert_roles = {
    UserRoles.ADMIN: 'Админ',
    UserRoles.MANAGER: 'Менеджер',
    UserRoles.USER: 'Пользователь',
}

convert_statuses = {
    TaskStatuses.OPEN: 'Открыта',
    TaskStatuses.WORK: 'В работе',
    TaskStatuses.COMPLETED: 'Завершена',
}


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
            team.role = convert_roles(team.role)
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

            role = await get_team_role(session, user.id, team_id)
            context['role'] = convert_roles[role]

            tasks = await task_service.get_tasks_by_team(team_id)
            for task in tasks:
                task.status = convert_statuses[task.status]
            context['tasks'] = tasks

            users = await team_service.get_users(team_id)
            for user in users:
                user.role = convert_roles[user.role]
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
