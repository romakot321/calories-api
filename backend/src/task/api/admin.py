from sqladmin import ModelView, expose
from starlette.requests import Request

from src.task.api.dependencies import get_task_uow
from src.task.infrastructure.db.orm import TaskDB


class TaskAdmin(ModelView, model=TaskDB):
    name = "Task"
    column_list = "__all__"

    @expose("/user/{user_id}", methods=["GET"], identity="admin:user:tasks")
    async def user_tasks(self, request: Request):
        user_id = request.path_params.get("user_id")
        if user_id is None:
            raise ValueError("user_id is none")

        uow = get_task_uow()
        async with uow:
            tasks = await uow.tasks.get_by_user_id(user_id)

        return await self.templates.TemplateResponse(request, "user_tasks.html", {"tasks": tasks})
