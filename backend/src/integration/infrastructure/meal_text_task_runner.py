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


class OpenaiMealTextTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
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
Determine the nutritional content (calories, proteins, fats, carbohydrates, fiber), ingredients, and weight of combined dishes from a user input. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on whether the dish is healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy.
Unhealthy items include foods high in added sugars, saturated or trans fats, salt, processed foods, and foods with artificial additives.
Analyze the meal for compliance with the plate rule and provide what is included and what needs to be added.

---

# Steps

1. Analyze the user input to identify the main ingredients of all dishes and estimate their weight, proteins, fats, carbohydrates and fiber.
2. Combine dishes if they belong to the same bowl/plate.
3. Calculate total calories and proportions of **proteins, fats, carbohydrates, fiber** based on estimated ingredients and weight (КБЖУ с точностью до грамма).
4. Determine the total weight of the combined dish with gram precision.
5. Assign a general name in {language} to the combined dish.
6. Provide a commentary categorizing the dish as healthy or unhealthy:

   * If healthy — praise the dish.
   * If unhealthy — offer friendly, supportive moderation advice and outline possible consequences gently.
   * Include plate rule analysis inside triple backticks:

     * Score the dish from **1 to 5**, where **1 = no compliance**, **5 = perfect compliance**.
     * If the score is not 5, describe what should be added (e.g., vegetables, protein, complex carbs).
     * Example:

       ```
       Блюдо соответствует правилу тарелки на 1/5. Белков достаточно, но необходимо добавить больше овощей.
       ```

---

# Output Format (JSON)
{
  "dishes": [
    {
      "name": "...",
      "ingredients": [
        {
          "name": "...",
          "weight": 0.0,
          "calories": 0.0,
          "protein": 0.0,
          "fats": 0.0,
          "carbohydrates": 0.0,
          "fiber": 0.0
        }
      ],
      "calories": 0.0,
      "protein": 0.0,
      "fats": 0.0,
      "carbohydrates": 0.0,
      "fiber": 0.0
      "weight": 0.0,
      "commentary": "..."
    }
  ]
}
"""
