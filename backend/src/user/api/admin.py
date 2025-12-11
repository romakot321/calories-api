from sqladmin import ModelView

from src.user.infrastructure.models import UserDB


class UserAdmin(ModelView, model=UserDB):
    name = "User"
    column_list = "__all__"
