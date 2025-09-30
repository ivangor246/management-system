from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

from .utils import get_context

templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter(dependencies=[Depends(get_context)])


@front_router.get('/', response_class=HTMLResponse)
async def home_page(request: Request, session: AsyncSession = Depends(get_session)):
    teams = []
    user = request.state.context.get('user')
    if user:
        from app.managers.teams import get_team_manager
        from app.schemas.teams import UserRoles
        from app.services.teams import get_team_service

        team_manager = get_team_manager(session)
        team_service = get_team_service(team_manager)

        teams = await team_service.get_teams_by_user(user.id)
        for team in teams:
            if team.role == UserRoles.ADMIN:
                team.role = 'Админ'
            elif team.role == UserRoles.MANAGER:
                team.role = 'Менеджер'
            else:
                team.role = 'Пользователь'
        request.state.context['teams'] = teams

    return templates.TemplateResponse('home.html', {'request': request, 'context': request.state.context})


@front_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'context': request.state.context})


@front_router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'context': request.state.context})
