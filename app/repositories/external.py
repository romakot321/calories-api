import os
from typing import BinaryIO
from openai import AsyncOpenAI
from loguru import logger
import httpx
import asyncio
import base64
import json
import aiohttp
import io


class ExternalRepository:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.deepseek_client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_TOKEN"), base_url="https://api.deepseek.com")

    async def send(self, image_raw: bytes, user_token: str) -> dict | None:
        image = io.BytesIO(image_raw)
        image.name = "a.jpg"
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                "https://api.logmeal.com/v2/image/segmentation/complete",
                headers={"Authorization": "Bearer " + user_token},
                data={"image": image}
            )
            assert resp.status == 200, await resp.text()
            body = await resp.json()

            resp = await session.post(
                "https://api.logmeal.com/v2/recipe/nutritionalInfo",
                headers={"Authorization": "Bearer " + user_token},
                json={"imageId": body["imageId"]}
            )
            assert resp.status == 200, await resp.text()
            body = await resp.json()

        logger.debug(f"Get image response: {body}")
        return body

    async def send_audio(self, audio_raw: BinaryIO) -> dict | None:
        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_raw,
            language="ru",
            prompt="Описание занятий спортом и съеденной еды",
        )

        logger.debug(f"Get response: {response}")
        return {"text": response.text}

    async def extract_food_names(self, text: str) -> list[dict]:
        response = await self.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                    {
                        "role": "system",
                        "content": "Найди все названия блюд, их размер и что с ними делать в вводе пользователя. Ответь по следующей json-схеме:" \
                                '{"food": [{"name": "название блюда", "size": размер, "action": действие}]}. Если размер не найден, оставляй поле пустым. Размер - только число граммов' \
                                ', если размер передан словом, вычисли общепринятый размер. Например, банка - 300 грамм.' \
                                '. Action - строго "добавить" или "удалить". Добавить значит добавить продукт в список, удалить - убрать из него. Если определить action не удалось, то пустое'
                    },
                    {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.7,
            response_format={"type": "json_object"},
            stream=False
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)["food"]
        except json.JSONDecodeError:
            return None

    async def recognize_calories_from_text(self, text: str) -> list[dict]:
        response = await self.deepseek_client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник, анализирующий ввод пользователя. Тебе необходимо определить каждый перечисленный вид еды и его КБЖУ, и ответить в JSON формате по следующей схеме:" \
                            '{"items": [{"product": "определенная еда", "weight": вес в граммах, "kilocalories_per100g": число ккал, "fats_per100g": число жиров, "carbohydrates_per100g": число углеводов, "fiber_per100g": число белков}]}' \
                            'Числовые поля только положительные. Если еда не найдена, оставляй все поля равными 0',
                    },
                    {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.7,
            response_format={"type": "json_object"},
            stream=False
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)["items"]
        except json.JSONDecodeError:
            return None

    async def translate_meal_audio_response(self, text: str) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "Ты помощник, анализирующий ввод пользователя. Тебе необходимо определить каждый перечисленный вид еды, что с ним сделать и его КБЖУ, и ответить в JSON формате по следующей схеме:"
                            '{"items": [{"product": "определенная еда", "weight": вес в граммах, "kilocalories_per100g": число ккал, "proteins_per100g": число протеинов, "fats_per100g": число жиров, "carbohydrates_per100g": число углеводов, "fiber_per100g": число белка, "action": "действие"}]}'
                            'Числовые поля только положительные. Если еда не найдена, оставляй все поля равными 0. Action - строго "добавить" или "удалить". Добавить значит добавить продукт в список, удалить - убрать из него. Если пользователь сказал "замена", то пересчитывай значение КБЖУ для нового блюда. Если определить action не удалось, то пустое',
                        }
                    ],
                },
                {"role": "user", "content": [{"type": "text", "text": text}]},
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
                                        "product": {"type": "string"},
                                        "weight": {"type": "number"},
                                        "kilocalories_per100g": {"type": "number"},
                                        "proteins_per100g": {"type": "number"},
                                        "fats_per100g": {"type": "number"},
                                        "carbohydrates_per100g": {"type": "number"},
                                        "action": {"type": "string"},
                                        "fiber_per100g": {"type": "number"},
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
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["items"],
                        "additionalProperties": False,
                    },
                },
            },
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
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
                            "text": 'Ты помощник, анализирующий ввод пользователя. Тебе необходимо определить каждый перечисленный вид спорта и его продолжительность занятия, и ответить в JSON формате по следующей схеме: {"items": [{"sport": "определенный спорт", "length": "продолжительность"}]}. Поле sport - только общепринятое употребление в изначальной форме, поле length - только положительное целое число секунд.',
                        }
                    ],
                },
                {"role": "user", "content": [{"type": "text", "text": text}]},
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
                                        "sport": {"type": "string"},
                                        "length": {"type": "number"},
                                    },
                                    "required": ["sport", "length"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["items"],
                        "additionalProperties": False,
                    },
                },
            },
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return None
