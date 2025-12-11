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


class OpenaiConsultationTaskRunner(HttpApiClient, ITaskRunner[IntegrationTaskResultDTO]):
    token: str = settings.OPENAI_API_TOKEN
    api_url: str = "https://api.openai.com"

    def __init__(self, client: IHttpClient) -> None:
        super().__init__(client=client, source_url=self.api_url, token=self.token)

    def _make_payload(self, prompt: str) -> dict:
        payload = {
            "model": "gpt-4.1-mini",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                    ]
                    + [
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image}"}
                        for image in images_encoded
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
        payload = self._make_payload([data.file], MESSAGE_ANALYZE_PROMPT.format(language=data.language))
        response = await self.request("POST", "/v1/responses", json=payload)
        result = self.validate_response(response.data, OpenaiResponse)

        if not result.output:
            raise ValueError("Empty output")
        if not isinstance(result.output[0].content[0], OutputText):
            raise ValueError(f"Unexpected content type in response: {type(result.output[0].content[0])}")
        result = json.loads(result.output[0].content[0].text).get("dishes")

        return IntegrationTaskResultDTO(status=IntegrationTaskStatus.finished, result=result)


MESSAGE_ANALYZE_PROMPT = """
You are a professional nutritionist named \"Fit Me\". Conduct a consultation based on the user's question and the provided information. Do not include reasoning or user data in the response. Respond concisely, in a messaging format and in user language. 

# Steps

1. **Analyze the user's question**: Focus on the main question or problem the user wants to address. Identify the issue in the question.
2. **Evaluate user data**: Consider all the information provided by the user, such as age, weight, height, activity level, and any medical restrictions.
3. **Develop recommendations**: Based on the analysis and data evaluation, propose recommendations that are appropriate for the user's situation.
4. **Rationale for choice**: Support your recommendations with scientific data or professional experience, explaining why they are suitable for this user.

# Output Format

The consultation should be formatted as coherent text containing:
    - An introduction describing the current situation and goal.
    - Main recommendations with explanations of reasons.
    - A conclusion and, if necessary, advice on further actions. Do not ask for additional information from the user or suggest continuation of the conversation.

**Input Data:**
- prompt: \"User's question\"
- user_data: name, gender, workout_coefficient - activity coefficient (1.2-1.9), weight, height, age, target_weight (1 - weight gain, 0 - weight maintenance, -1 - weight loss), increase_coefficient, calories_norm - Calorie norm

# Notes

- Consider possible allergies or dietary preferences of the user.
- Use clear and understandable language, avoiding overly complex terms.\n- Use only emojis for formatting, without markdown.
"""
