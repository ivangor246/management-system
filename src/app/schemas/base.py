from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseModelSchema(BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


class BaseCreateSchema(BaseSchema): ...


class BaseUpdateSchema(BaseSchema): ...


class BaseResponseSchema(BaseSchema):
    success: bool = True
    detail: str = 'Success response'
