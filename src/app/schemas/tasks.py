from datetime import date
from enum import Enum

from .base import BaseCreateSchema, BaseResponseSchema


class TaskStatuses(str, Enum):
    OPEN = 'o'
    WORK = 'w'
    COMPLETED = 'c'


class TaskCreateSchema(BaseCreateSchema):
    description: str
    deadline: date
    status: TaskStatuses
    performer_id: int | None


class TaskCreateSuccessSchema(BaseResponseSchema):
    task_id: int
    detail: str = 'The task was successfully created'
