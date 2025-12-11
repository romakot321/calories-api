from fastapi import FastAPI

from src.db.engine import engine
from src.task.api.rest import router as task_router
from src.user.api.rest import router as user_router
import src.core.logging_setup
from src.core.logging_setup import setup_fastapi_logging

app = FastAPI(title="Calories API")
setup_fastapi_logging(app)

app.include_router(task_router, tags=["Task"], prefix="/api/task")
app.include_router(user_router, tags=["User"], prefix="/api/user")

from sqladmin import Admin
from src.core.admin import authentication_backend
from src.task.api.admin import TaskAdmin
from src.user.api.admin import UserAdmin

admin = Admin(app, engine=engine, authentication_backend=authentication_backend)
admin.add_view(TaskAdmin)
admin.add_view(UserAdmin)
