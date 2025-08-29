from datetime import date
from enum import Enum

from pydantic import Field

from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema, BaseUpdateSchema


class TaskStatuses(str, Enum):
    OPEN = 'o'
    WORK = 'w'
    COMPLETED = 'c'


class TaskSchema(BaseModelSchema):
    description: str
    deadline: date
    status: TaskStatuses
    performer_id: int | None
    team_id: int
    score: int | None


class TaskCreateSchema(BaseCreateSchema):
    description: str
    deadline: date
    status: TaskStatuses = TaskStatuses.OPEN
    performer_id: int | None = Field(ge=1, default=None)


class TaskCreateSuccessSchema(BaseResponseSchema):
    task_id: int
    detail: str = 'The task has been successfully created'


class TaskUpdateSchema(BaseUpdateSchema):
    description: str | None = None
    deadline: date | None = None
    status: TaskStatuses | None = None
    performer_id: int | None = None


class TaskUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The task has been successfully updated'


class TaskScoreSchema(BaseUpdateSchema):
    score: int = Field(ge=1, le=5)


class TaskScoreSuccessSchema(BaseResponseSchema):
    detail: str = 'The task score has been successfully updated'
