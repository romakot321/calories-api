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
        self.deepseek_client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_TOKEN"), base_url="https://api.deepseek.com"
        )

    async def send(self, image_raw: bytes) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "Determine the nutritional content (calories, proteins, fats, carbohydrates), ingredients, and weight of combined dishes from a photo. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on the nutritional value and benefits of the presented food.\n\n# Steps\n\n1. Analyze the photo to identify the main ingredients of all dishes and estimate their weight.\n2. Combine some of dishes if they in the same bowl.\n3. Calculate the total calories and the proportions of proteins, fats, and carbohydrates for the combined dish based on identified ingredients and their weight.\n4. Determine the total weight of the combined dish with gram precision.\n5. Assign a general name in Russian to the combined dish.\n6. Provide a brief commentary on the nutritional properties and health benefits of the combined dish.\n\n# Output Format\n\nProvide the output in JSON format:\n- `dishes`: an list of objects representing the dishes containing:\n    - `dish_name`: the general name in Russian of the combined dish.\n    - `ingredients`: a list of objects in Russian for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n    - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n    - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with похвалой или замечениями пользователя по поводу combined dish. Варьируйте текст, используя эмодзи.\n\n# Notes\n\n- Consider possible distortions due to photo quality.\n- Make the best guesses for unidentified ingredients.\n- Include general health benefits context when applicable.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64,"
                                + base64.b64encode(image_raw).decode()
                            },
                        }
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return None

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
                    "content": "Найди все названия блюд, их размер и что с ними делать в вводе пользователя. Ответь по следующей json-схеме:"
                    '{"food": [{"name": "название блюда", "size": размер, "action": действие}]}. Если размер не найден, оставляй поле пустым. Размер - только число граммов'
                    ", если размер передан словом, вычисли общепринятый размер. Например, банка - 300 грамм."
                    '. Action - строго "добавить" или "удалить". Добавить значит добавить продукт в список, удалить - убрать из него. Если определить action не удалось, то пустое',
                },
                {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.7,
            response_format={"type": "json_object"},
            stream=False,
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)["food"]
        except json.JSONDecodeError:
            return None

    async def recognize_calories_from_text(self, text: str) -> list[dict]:
        response = await self.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Determine the nutritional content (calories, proteins, fats, carbohydrates), ingredients, and weight of combined dishes from a photo. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on the nutritional value and benefits of the presented food.\n\n# Steps\n\n1. Analyze the photo to identify the main ingredients of all dishes and estimate their weight.\n2. Combine some of dishes if they in the same bowl.\n3. Calculate the total calories and the proportions of proteins, fats, and carbohydrates for the combined dish based on identified ingredients and their weight.\n4. Determine the total weight of the combined dish with gram precision.\n5. Assign a general name in Russian to the combined dish.\n6. Provide a brief commentary on the nutritional properties and health benefits of the combined dish.\n\n# Output Format\n\nProvide the output in JSON format:\n- `dishes`: an list of objects representing the dishes containing:\n    - `dish_name`: the general name in Russian of the combined dish.\n    - `ingredients`: a list of objects in Russian for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n    - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n    - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with похвалой или замечениями пользователя по поводу combined dish. Варьируйте текст, используя эмодзи.\n\n# Notes\n\n- Consider possible distortions due to photo quality.\n- Make the best guesses for unidentified ingredients.\n- Include general health benefits context when applicable.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.7,
            response_format={"type": "json_object"},
            stream=False,
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
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

    async def edit_meal_text(self, meal_json: str, text: str) -> list[dict]:
        response = await self.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": 'Modify the nutritional values (calories, proteins, fats, and carbohydrates) and the dish or ingredient composition based on user input within a JSON structure.\n\nReceive a JSON structure containing nutritional information for a dish and its ingredients. Accept user input to specify changes, which may include adding, removing, or replacing entire dishes or specific ingredients, along with recalculating their nutritional values. Implement these changes while ensuring the data remains correctly formatted.\n\n# Steps\n\n1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.\n2. Receive input from the user specifying changes, which may involve:\n   - Altering nutritional values (e.g., calories, proteins) for existing items.\n   - Adding new dishes or ingredients with specified nutritional values.\n   - Removing existing dishes or ingredients.\n   - Replacing existing dishes or ingredients with new ones.\n3. Apply the specified changes to the corresponding fields in the JSON data.\n4. Recalculate the total nutritional values with gram precision (calories, proteins, fats, and carbohydrates) to ensure consistency.\n5. Rewrite "comment" field for new dishes.\n6. Ensure that all data remains in the correct format.\n\n# Output Format\n\nReturn the updated data in JSON format without using code blocks.\n\n# Notes\n\n- Ensure that changes match the user\'s request exactly',
                },
                {"role": "user", "content": "JSON data: " + meal_json},
                {"role": "user", "content": "User input: " + text},
            ],
            max_tokens=2048,
            temperature=0.7,
            response_format={"type": "json_object"},
            stream=False,
        )

        logger.debug(f"Get response: {response}")
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return None
