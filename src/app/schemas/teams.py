from enum import Enum

from .base import BaseCreateSchema, BaseModelSchema, BaseResponseSchema, BaseSchema, BaseUpdateSchema


class UserRoles(str, Enum):
    USER = 'u'
    MANAGER = 'm'
    ADMIN = 'a'


# UserTeam
class UserTeamSchema(BaseModelSchema):
    user_id: int
    team_id: int
    role: UserRoles


class TeamMemberSchema(BaseSchema):
    user_id: int
    username: str
    role: UserRoles


class TeamByMemberSchema(BaseSchema):
    team_id: int
    name: str
    role: UserRoles


class UserTeamCreateSchema(BaseCreateSchema):
    user_id: int
    role: UserRoles = UserRoles.USER


class UserTeamCreateSuccessSchema(BaseResponseSchema):
    detail: str = 'The user has been successfully added to the team'


class UserTeamUpdateSchema(BaseUpdateSchema):
    role: UserRoles


class UserTeamUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The user role has been successfully changed'


# Team
class TeamSchema(BaseModelSchema):
    name: str
    members: list['UserTeamSchema'] = []


class TeamCreateSchema(BaseCreateSchema):
    name: str


class TeamCreateSuccessSchema(BaseResponseSchema):
    team_id: int
    detail: str = 'The team has been successfully created'


class TeamUpdateSchema(BaseUpdateSchema):
    name: str


class TeamUpdateSuccessSchema(BaseResponseSchema):
    detail: str = 'The team has been successfully updated'
