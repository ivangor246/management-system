"""
Admin views for SQLAdmin.

This module defines the admin interface views for all main models,
customizing which columns are displayed in the admin panel.
"""

from sqladmin import ModelView

from app.models.comments import Comment
from app.models.meetings import Meeting
from app.models.tasks import Task
from app.models.teams import Team, UserTeam
from app.models.users import User


class UserAdmin(ModelView, model=User):
    """
    Admin view for the User model.
    Displays basic user information and status flags.
    """

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
    """
    Admin view for the Team model.
    Displays the team name.
    """

    column_list = [Team.name]


class UserTeamAdmin(ModelView, model=UserTeam):
    """
    Admin view for the UserTeam association model.
    Displays the user, team, and role relationships.
    """

    column_list = [
        UserTeam.user_id,
        UserTeam.team_id,
        UserTeam.role,
    ]


class TaskAdmin(ModelView, model=Task):
    """
    Admin view for the Task model.
    Displays task description, deadline, status, performer, and team.
    """

    column_list = [
        Task.description,
        Task.deadline,
        Task.status,
        Task.performer_id,
        Task.team_id,
    ]


class CommentAdmin(ModelView, model=Comment):
    """
    Admin view for the Comment model.
    Displays comment text, associated user, and task.
    """

    column_list = [
        Comment.text,
        Comment.user_id,
        Comment.task_id,
    ]


class MeetingAdmin(ModelView, model=Meeting):
    """
    Admin view for the Meeting model.
    Displays meeting name, date, time, team, and participating users.
    """

    column_list = [
        Meeting.name,
        Meeting.date,
        Meeting.time,
        Meeting.team_id,
        Meeting.users,
    ]
