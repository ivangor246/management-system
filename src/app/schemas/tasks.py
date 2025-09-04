from datetime import date
from enum import Enum

from pydantic import Field, model_validator

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
    evaluation: int | None

    @model_validator(mode='before')
    def extract_evaluation(cls, values):
        evaluation_obj = getattr(values, 'evaluation', None)
        if evaluation_obj is not None:
            values_dict = values.__dict__.copy()
            values_dict['evaluation'] = evaluation_obj.value
            return values_dict
        return values


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
