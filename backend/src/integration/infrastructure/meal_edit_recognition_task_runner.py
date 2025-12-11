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


class OpenaiMealEditRecognitionTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
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
                    "name": "dishes",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dishes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "ingredients": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "weight": {"type": "number"},
                                                    "calories": {"type": "number"},
                                                    "protein": {"type": "number"},
                                                    "fats": {"type": "number"},
                                                    "carbohydrates": {"type": "number"},
                                                    "fiber": {"type": "number"},
                                                },
                                                "required": ["name", "weight", "calories", "protein", "fats", "carbohydrates", "fiber"],
                                                "additionalProperties": False,
                                            },
                                        },
                                        "calories": {"type": "number"},
                                        "protein": {"type": "number"},
                                        "fats": {"type": "number"},
                                        "carbohydrates": {"type": "number"},
                                        "fiber": {"type": "number"},
                                        "weight": {"type": "number"},
                                        "commentary": {"type": "string"},
                                    },
                                    "required": ["name", "ingredients", "calories", "protein", "fats", "carbohydrates", "fiber", "weight", "commentary"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["dishes"],
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
        result = json.loads(result.output[0].content[0].text).get("dishes")

        return IntegrationTaskResultDTO(status=IntegrationTaskStatus.finished, result=result)


MESSAGE_ANALYZE_PROMPT = """
JSON format:
    - `dishes`: a list of objects representing the dishes containing:
    - `dish_name`: the general name in {language} of the combined dish.
    - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient_name` and `weight`, `calories`, `protein`, `fats`, `carbohydrates`, `fiber` fields.
    - `calories`, `protein`, `fats`, `carbohydrates`, `fiber` calculated with gram precision.
    - `weight`: the total weight of the combined dish with gram precision.
    - `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.

Modify the nutritional values (calories, proteins, fats, and carbohydrates) and the dish or ingredient composition and a commentary in {language} language on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Update is based on user input within a JSON structure.

Receive a JSON structure containing nutritional information for a dish and its ingredients. Accept user input to specify changes, which may include adding, removing, or replacing entire dishes or specific ingredients, along with recalculating their nutritional values. Implement these changes while ensuring the data remains correctly formatted.

# Steps

1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.
2. Receive input from the user specifying changes, which may involve:
    - Altering nutritional values with gram precision (e.g., calories, proteins) for existing items.
    - Adding new dishes or ingredients with calculated nutritional values.
    - Removing existing dishes or ingredients.
    - Replacing existing dishes or ingredients with new ones.
3. Apply the specified changes to the corresponding fields in the JSON data.
4. Recalculate the total nutritional values with gram precision (calories, proteins, fats, and carbohydrates) to ensure consistency.
5. Rewrite "commentary" field for new dishes, use emojis.
6. Ensure that all data remains in the correct format.

# Output Format

Return the updated data in JSON format without using code blocks.

# Notes

- Ensure that changes match the user's request exactly
"""
