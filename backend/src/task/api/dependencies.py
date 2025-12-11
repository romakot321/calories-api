from typing import Annotated

from fastapi import Depends

from src.core.http.client import IHttpClient
from src.core.http.dependencies import get_http_client
from src.integration.api.dependencies import get_integration_meal_audio_task_runner, get_integration_meal_edit_recognition_task_runner, get_integration_meal_image_task_runner, get_integration_meal_text_task_runner, get_integration_sport_audio_task_runner, get_integration_sport_edit_recognition_task_runner, get_integration_sport_text_task_runner
from src.task.infrastructure.db.unit_of_work import TaskUnitOfWork
from src.task.application.interfaces.task_uow import ITaskUnitOfWork
from src.task.application.interfaces.task_runner import ITaskRunner


def get_task_uow() -> ITaskUnitOfWork:
    return TaskUnitOfWork()


TaskUoWDepend = Annotated[ITaskUnitOfWork, Depends(get_task_uow)]
TaskImageMealRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_meal_image_task_runner)]
TaskTextMealRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_meal_text_task_runner)]
TaskAudioMealRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_meal_audio_task_runner)]
TaskEditMealRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_meal_edit_recognition_task_runner)]
TaskTextSportRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_sport_text_task_runner)]
TaskAudioSportRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_sport_audio_task_runner)]
TaskEditSportRunnerDepend = Annotated[ITaskRunner, Depends(get_integration_sport_edit_recognition_task_runner)]
HttpClientDepend = Annotated[IHttpClient, Depends(get_http_client)]
