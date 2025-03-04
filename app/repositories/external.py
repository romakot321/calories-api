from typing import BinaryIO
from openai import AsyncOpenAI
from loguru import logger
import httpx
import asyncio
import base64
import json


class ExternalRepository:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def _run(self, image: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                "role": "system",
                "content": [
                    {
                    "type": "text",
                    # "text": "Analyze the provided food photo and estimate the total calories along with a breakdown of each detected food item. Use the following JSON structure for the response:\n\n{\n  \"items\": [\n    {\n      \"name\": \"food_item_name\",\n      \"quantity\": \"estimated_quantity_in_grams_or_units\",\n      \"estimated_calories\": number,\n      \"confidence\": \"high/medium/low\"\n    }\n  ],\n  \"total_calories\": number,\n  \"error\": null | \"message_if_no_food_detected\"\n}\n\nGuidelines:\n1. Prioritize common food recognition and portion estimation.\n2. Include confidence levels based on visual clarity.\n3. If uncertain, return 'error' with a brief reason.\n4. Do not include explanations—only JSON."
                    "text": "Analyze the provided food photo and return nutritional information. Translate product name to russian. Use this JSON structure:\n\n{\n  \"items\": [\n    {\n      \"product\": \"identified_food_name\",\n      \"weight\": estimated_weight_in_grams,\n      \"kilocalories_per100g\": int,\n      \"proteins_per100g\": int,\n      \"fats_per100g\": int,\n      \"carbohydrates_per100g\": int,\n      \"fiber_per100g\": int,\n      \"confidence\": \"high/medium/low\"\n    }\n  ],\n  \"total_kilocalories\": sum_of_all_items_kcal,\n  \"error\": null | \"brief_error_message\"\n}\n\nGuidelines:\n1. Estimate weight and nutritional values per 100g\n2. Calculate total kcal: (kilocalories_per100g * weight / 100)\n3. Include confidence for identification accuracy\n4. Return error if food unclear\n5. Only JSON output, no explanations"
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64," + image
                    }
                    }
                ]
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0.2,
            max_completion_tokens=4000,
            top_p=0.3,
            frequency_penalty=0,
            presence_penalty=0
        )
        logger.debug(f"Get response: {response}")
        return response.choices[0].message.content

    async def send(self, image_raw: bytes) -> dict | None:
        response = await self._run(base64.b64encode(image_raw).decode())
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    async def send_audio(self, audio_raw: BinaryIO) -> dict | None:
        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_raw,
            language="ru",
            prompt="Описание занятий спортом и съеденной еды"
        )

        logger.debug(f"Get response: {response}")
        return {"text": response.text}

    async def translate_meal_audio_response(self, text: str) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                "role": "system",
                "content": [
                    {
                    "type": "text",
                    "text": 'Ты помощник, анализирующий ввод пользователя. Тебе необходимо определить каждый перечисленный вид еды, что с ним сделать и его КБЖУ, и ответить в JSON формате по следующей схеме:' \
                            '{"items": [{"product": "определенная еда", "weight": вес в граммах, "kilocalories_per100g": число ккал, "proteins_per100g": число протеинов, "fats_per100g": число жиров, "carbohydrates_per100g": число углеводов, "fiber_per100g": число белка, "action": "действие"}]}' \
                            'Числовые поля только положительные. Если еда не найдена, оставляй все поля равными 0. Action - строго "добавить" или "удалить". Добавить значит добавить продукт в список, удалить - убрать из него. При замене продукта копируй объем блюда, но пересчитывай значение КБЖУ. Если определить action не удалось, то пустое'
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": text
                    }
                ]
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                "name": "sport_metadata",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product": {
                                    "type": "string"
                                },
                                "weight": {
                                    "type": "number"
                                },
                                "kilocalories_per100g": {
                                    "type": "number"
                                },
                                "proteins_per100g": {
                                    "type": "number"
                                },
                                "fats_per100g": {
                                    "type": "number"
                                },
                                "carbohydrates_per100g": {
                                    "type": "number"
                                },
                                "action": {
                                    "type": "string"
                                },
                                "fiber_per100g": {
                                    "type": "number"
                                }
                            },
                            "required": [
                                "product",
                                "weight",
                                "action",
                                "kilocalories_per100g",
                                "proteins_per100g",
                                "fats_per100g",
                                "carbohydrates_per100g",
                                "fiber_per100g",
                            ],
                            "additionalProperties": False
                        }
                    }
                    },
                    "required": [
                    "items"
                    ],
                    "additionalProperties": False
                }
                }
            },
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return None

    async def translate_sport_audio_response(self, text: str) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                "role": "system",
                "content": [
                    {
                    "type": "text",
                    "text": "Ты помощник, анализирующий ввод пользователя. Тебе необходимо определить каждый перечисленный вид спорта и его продолжительность занятия, и ответить в JSON формате по следующей схеме: {\"items\": [{\"sport\": \"определенный спорт\", \"length\": \"продолжительность\"}]}. Поле sport - только общепринятое употребление в изначальной форме, поле length - только положительное целое число секунд."
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": text
                    }
                ]
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                "name": "sport_metadata",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "sport": {
                            "type": "string"
                            },
                            "length": {
                            "type": "number"
                            }
                        },
                        "required": [
                            "sport",
                            "length"
                        ],
                        "additionalProperties": False
                        }
                    }
                    },
                    "required": [
                    "items"
                    ],
                    "additionalProperties": False
                }
                }
            },
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return None

