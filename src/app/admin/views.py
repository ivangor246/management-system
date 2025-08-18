from sqladmin import ModelView

from app.models.comments import Comment
from app.models.tasks import Task
from app.models.teams import Team, UserTeam
from app.models.users import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        User.is_admin,
        User.is_available,
    ]


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.name]


class UserTeamAdmin(ModelView, model=UserTeam):
    column_list = [
        UserTeam.user_id,
        UserTeam.team_id,
        UserTeam.role,
    ]


class TaskAdmin(ModelView, model=Task):
    column_list = [
        Task.description,
        Task.deadline,
        Task.status,
        Task.performer_id,
        Task.team_id,
    ]


class CommentAdmin(ModelView, model=Comment):
    column_list = [
        Comment.text,
        Comment.user_id,
        Comment.task_id,
    ]
