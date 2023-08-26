import sys
sys.path.append('..')
from typing import Optional, Annotated
from starlette import status
from fastapi import Depends, HTTPException, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from routers.auth import get_current_user
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory='templates')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    priority: int = Field(ge=0, le=5)
    complete: bool = Field(default=False)
    owner_id: int = Field(default=1)


@router.get("/")
async def read_all_by_user(req: Request, db: db_dependency):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get('id')).all()
    return templates.TemplateResponse("home.html", {"request": req, "todos": todos, 'user': user})


@router.get("/add-todo")
async def add_todo(req: Request):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('add-todo.html', {'request': req, 'user': user})


@router.post("/add-todo")
async def create_todo(req: Request, db: db_dependency, title: Annotated[str, Form()],
                      description: Annotated[str, Form()], priority: Annotated[int, Form()]):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.complete = False
    todo_model.priority = priority
    todo_model.owner_id = user.get('id')
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)


@router.get("/edit-todo/{todo_id}")
async def edit_todo(req: Request, todo_id: int, db: db_dependency):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return templates.TemplateResponse('edit-todo.html', {'request': req, 'todo': todo, 'user': user})


@router.post("/edit-todo/{todo_id}")  # When using forms only get and post method available no put
async def edit_todo_commit(req: Request, todo_id: int, db: db_dependency,
                           title: Annotated[str, Form()],
                           description: Annotated[str, Form()],
                           priority: Annotated[int, Form()]):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/delete-todo/{todo_id}")
async def delete_todo(req: Request, db: db_dependency, todo_id: int):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_400_BAD_REQUEST)
    db.delete(todo_model)
    db.commit()
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)


@router.get("/complete-todo/{todo_id}")
async def complete_todo(req: Request, db: db_dependency, todo_id: int):
    user = await get_current_user(req)
    if user is None:
        return RedirectResponse(url='/auth/', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == 1).first()
    todo_model.complete = not todo_model.complete
    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_400_BAD_REQUEST)
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

