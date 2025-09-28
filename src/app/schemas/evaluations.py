from pydantic import Field

from .base import BaseResponseSchema, BaseUpdateSchema


class EvaluationSchema(BaseUpdateSchema):
    value: int = Field(ge=1, le=5)


class EvaluationSuccessSchema(BaseResponseSchema):
    detail: str = 'The task evaluation has been successfully updated'
