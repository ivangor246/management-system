from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


async def get_is_auth(request: Request) -> bool:
    token = request.cookies.get('access_token')
    request.state.is_auth = bool(token)
    return request.state.is_auth


templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter(dependencies=[Depends(get_is_auth)])


@front_router.get('/', response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse('home.html', {'request': request, 'is_auth': request.state.is_auth})


@front_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'is_auth': request.state.is_auth})


@front_router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'is_auth': request.state.is_auth})
