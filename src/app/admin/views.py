from sqladmin import ModelView

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
