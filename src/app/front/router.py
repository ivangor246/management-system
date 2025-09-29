from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .utils import get_context

templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter(dependencies=[Depends(get_context)])


@front_router.get('/', response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse('home.html', {'request': request, 'context': request.state.context})


@front_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'context': request.state.context})


@front_router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'context': request.state.context})
