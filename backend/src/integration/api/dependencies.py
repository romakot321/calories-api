from src.core.http.client import AsyncHttpClient
from src.integration.infrastructure.meal_audio_task_runner import OpenaiMealAudioTaskRunner
from src.integration.infrastructure.meal_edit_recognition_task_runner import OpenaiMealEditRecognitionTaskRunner
from src.integration.infrastructure.meal_image_task_runner import OpenaiMealImageTaskRunner
from src.integration.infrastructure.meal_text_task_runner import OpenaiMealTextTaskRunner
from src.integration.infrastructure.sport_audio_task_runner import OpenaiSportAudioTaskRunner
from src.integration.infrastructure.sport_edit_recognition_task_runner import OpenaiSportEditRecognitionTaskRunner
from src.integration.infrastructure.sport_text_task_runner import OpenaiSportTextTaskRunner
from src.task.application.interfaces.task_runner import ITaskRunner


def get_integration_meal_image_task_runner() -> ITaskRunner:
    return OpenaiMealImageTaskRunner(AsyncHttpClient())


def get_integration_meal_text_task_runner() -> ITaskRunner:
    return OpenaiMealTextTaskRunner(AsyncHttpClient())


def get_integration_meal_audio_task_runner() -> ITaskRunner:
    return OpenaiMealAudioTaskRunner(AsyncHttpClient())


def get_integration_meal_edit_recognition_task_runner() -> ITaskRunner:
    return OpenaiMealEditRecognitionTaskRunner(AsyncHttpClient())


def get_integration_sport_text_task_runner() -> ITaskRunner:
    return OpenaiSportTextTaskRunner(AsyncHttpClient())


def get_integration_sport_audio_task_runner() -> ITaskRunner:
    return OpenaiSportAudioTaskRunner(AsyncHttpClient())


def get_integration_sport_edit_recognition_task_runner() -> ITaskRunner:
    return OpenaiSportEditRecognitionTaskRunner(AsyncHttpClient())
