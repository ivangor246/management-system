import datetime

from pydantic import Field

from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema, BaseUpdateSchema
from .users import UserSchema


class MeetingSchema(BaseModelSchema):
    name: str
    date: datetime.date
    time: datetime.time
    team_id: int
    users: list['UserSchema']


class MeetingCreateSchema(BaseCreateSchema):
    name: str = Field(max_length=100)
    date: datetime.date
    time: datetime.time
    member_ids: list[int]


class MeetingCreateSuccessSchema(BaseResponseSchema):
    meeting_id: int
    detail: str = 'The meeting has been successfully created'


class MeetingUpdateSchema(BaseUpdateSchema):
    name: str | None = Field(default=None, max_length=100)
    date: datetime.date | None = None
    time: datetime.time | None = None
    member_ids: list[int] | None = None


class MeetingUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The meeting has been successfully updated'
