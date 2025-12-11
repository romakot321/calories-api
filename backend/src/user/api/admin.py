from typing import Any
from sqladmin import BaseView, ModelView, expose
from starlette.datastructures import URL
from starlette.requests import Request

from src.user.api.dependencies import get_user_uow
from src.user.infrastructure.models import UserDB


class UserAdmin(ModelView, model=UserDB):
    details_template = "users.html"
    name = "User"
    column_list = "__all__"

    def _build_url_for(self, name: str, request: Request, obj: Any) -> URL:
        if name == 'admin:user:tasks':
            return URL("/admin/task-db/user/" + obj.id)
        return super()._build_url_for(name, request, obj)
