from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory='app/front/templates')

front_router = APIRouter()


@front_router.get('/', response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse('home.html', {'request': request})


@front_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})
