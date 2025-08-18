from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema


class CommentSchema(BaseModelSchema):
    text: str
    user_id: int
    task_id: int


class CommentCreateSchema(BaseCreateSchema):
    text: str


class CommentCreateSuccessSchema(BaseResponseSchema):
    comment_id: int
    detail: str = 'Comment has been successfully created'
