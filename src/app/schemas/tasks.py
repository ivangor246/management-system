from datetime import date
from enum import Enum

from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema, BaseUpdateSchema


class TaskStatuses(str, Enum):
    OPEN = 'o'
    WORK = 'w'
    COMPLETED = 'c'


class TaskSchema(BaseModelSchema):
    description: str
    deadline: date
    status: TaskStatuses
    performer_id: int
    team_id: int


class TaskCreateSchema(BaseCreateSchema):
    description: str
    deadline: date
    status: TaskStatuses = TaskStatuses.OPEN
    performer_id: int | None


class TaskCreateSuccessSchema(BaseResponseSchema):
    task_id: int
    detail: str = 'The task has been successfully created'


class TaskUpdateSchema(BaseUpdateSchema):
    description: str | None
    deadline: date | None
    status: TaskStatuses | None
    performer_id: int | None


class TaskUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The task has been successfully updated'
