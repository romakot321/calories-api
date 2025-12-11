import base64
from io import BytesIO
import json

from src.core.config import settings
from src.core.http.client import IHttpClient
from src.integration.infrastructure.sport_text_task_runner import OpenaiSportTextTaskRunner
from src.task.domain.entities import TaskRun
from src.integration.domain.dtos import IntegrationTaskStatus, IntegrationTaskResultDTO
from src.core.http.api_client import HttpApiClient
from src.integration.domain.schemas import OpenaiResponse, OutputText, StructuredData
from src.task.application.interfaces.task_runner import ITaskRunner


class OpenaiSportAudioTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
    token: str = settings.OPENAI_API_TOKEN
    api_url: str = "https://api.openai.com"

    def __init__(self, client: IHttpClient) -> None:
        super().__init__(client=client, source_url=self.api_url, token=self.token)
        self.text_runner = OpenaiSportTextTaskRunner(client)

    async def start(self, data: TaskRun) -> IntegrationTaskResultDTO:
        if data.file is None:
            raise ValueError("Empty input")

        response = await self.multipart_request(
            "POST",
            "/v1/audio/translations",
            data={"model": "gpt-4o-transcribe", "prompt": MESSAGE_ANALYZE_PROMPT},
            files=[("file", data.file)],
        )
        result = self.validate_response(response.data, OpenaiResponse)

        if not result.output:
            raise ValueError("Empty output")
        if not isinstance(result.output[0].content[0], OutputText):
            raise ValueError(f"Unexpected content type in response: {type(result.output[0].content[0])}")
        result = result.output[0].content[0].text

        return await self.text_runner.start(TaskRun(language=data.language, text=result))


MESSAGE_ANALYZE_PROMPT = """Описание занятий спортом"""
