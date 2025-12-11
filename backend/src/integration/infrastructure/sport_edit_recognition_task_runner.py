import base64
from io import BytesIO
import json

from src.core.config import settings
from src.core.http.client import IHttpClient
from src.task.domain.entities import TaskRun
from src.integration.domain.dtos import IntegrationTaskStatus, IntegrationTaskResultDTO
from src.core.http.api_client import HttpApiClient
from src.integration.domain.schemas import OpenaiResponse, OutputText, StructuredData
from src.task.application.interfaces.task_runner import ITaskRunner


class OpenaiSportEditRecognitionTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
    token: str = settings.OPENAI_API_TOKEN
    api_url: str = "https://api.openai.com"

    def __init__(self, client: IHttpClient) -> None:
        super().__init__(client=client, source_url=self.api_url, token=self.token)

    def _make_payload(self, text: str, prompt: str) -> dict:
        payload = {
            "model": "gpt-4.1-mini",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_text", "text": text}
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "sports",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sports": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "length": {"type": "number"},
                                        "calories": {"type": "number"},
                                        "commentary": {"type": "string"},
                                    },
                                    "required": ["name", "calories", "length", "commentary"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["sports"],
                        "additionalProperties": False,
                    },
                }
            },
        }

        return payload

    async def start(self, data: TaskRun) -> IntegrationTaskResultDTO:
        if data.text is None:
            raise ValueError("Empty input")

        payload = self._make_payload(data.text, MESSAGE_ANALYZE_PROMPT.replace("{language}", data.language))
        response = await self.request("POST", "/v1/responses", json=payload)
        result = self.validate_response(response.data, OpenaiResponse)

        if not result.output:
            raise ValueError("Empty output")
        if not isinstance(result.output[0].content[0], OutputText):
            raise ValueError(f"Unexpected content type in response: {type(result.output[0].content[0])}")
        result = json.loads(result.output[0].content[0].text).get("sports")

        return IntegrationTaskResultDTO(status=IntegrationTaskStatus.finished, result=result)


MESSAGE_ANALYZE_PROMPT = """
JSON format:
    - `sports`: a list of objects representing the sports containing:
        - `name`: the general name in {language} of the sport.
        - `length`: duration in seconds of the sport.
        - `calories`: the total calories of the sport.

Modify the calories values or sports composition. Update is based on user input within a JSON structure.

Receive a JSON structure containing calories information for a sport. Accept user input to specify changes, which may include adding, removing, or replacing entire sport, along with recalculating their calories values. Implement these changes while ensuring the data remains correctly formatted.

# Steps

1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.
2. Receive input from the user specifying changes, which may involve:
    - Altering calories values with gram precision for existing items.
    - Adding new sports with calculated nutritional values.
    - Removing existing sports.
    - Replacing existing sports with new ones.
3. Apply the specified changes to the corresponding fields in the JSON data.
4. Recalculate the total calories values with gram precision to ensure consistency.
5. Ensure that all data remains in the correct format.

# Output Format

Return the updated data in JSON format without using code blocks.

# Notes

- Ensure that changes match the user's request exactly.
"""
