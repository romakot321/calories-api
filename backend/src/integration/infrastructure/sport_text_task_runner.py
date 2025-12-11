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


class OpenaiSportTextTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
    token: str = settings.OPENAI_API_TOKEN
    api_url: str = "https://api.openai.com"

    def __init__(self, client: IHttpClient) -> None:
        super().__init__(client=client, source_url=self.api_url, token=self.token)

    def _make_payload(self, text: str, prompt: str) -> dict:
        images_encoded = self._encode_images(images)
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

        payload = self._make_payload(data.text, MESSAGE_ANALYZE_PROMPT.format(language=data.language))
        response = await self.request("POST", "/v1/responses", json=payload)
        result = self.validate_response(response.data, OpenaiResponse)

        if not result.output:
            raise ValueError("Empty output")
        if not isinstance(result.output[0].content[0], OutputText):
            raise ValueError(f"Unexpected content type in response: {type(result.output[0].content[0])}")
        result = json.loads(result.output[0].content[0].text).get("sports")

        return IntegrationTaskResultDTO(status=IntegrationTaskStatus.finished, result=result)


MESSAGE_ANALYZE_PROMPT = """
Identify all sports mentioned in the given text, and specify the duration of each activity and the exact number of calories burned. Compile this information into a JSON structure with very accurate calorie estimations.

# Steps

1. Read the provided text.
2. Identify all mentioned sports and their duration in seconds. If the duration is given in repetitions, calculate the total exercise time.
3. For each sport, calculate the number of calories burned in kcal. Ensure that the calculations are very precise.
4. Populate the JSON structure with the listed attributes for each sport.

# Output Format

Present the result in a JSON list format with the keys "comment" and "items", where each element will be a sport object with the following keys:
    - "name": Name of the sport in {language} language.
    - "length": Duration of the activity in seconds.
    - "calories": Number of calories burned with high accuracy.
    - "commentary": commentary about identified sport, mention what is provided sport good for and praise user. Use emojis and motivate user.

# Notes

- If the text poses challenges in identifying the sport, consult the context or provided units.
- Ensure the JSON structure is correctly opened and closed, and all keys contain relevant information.
- Prioritize accuracy in the calorie calculation, considering detailed factors such as activity intensity and possible provided user characteristics.
"""
