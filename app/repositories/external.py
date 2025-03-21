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

    async def send(self, image_raw: bytes, language: str) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Determine the nutritional content (calories, proteins, fats, carbohydrates), ingredients, and weight of combined dishes from a photo. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Unhealthy items include: Foods high in added sugars, Foods high in saturated and trans fats, Foods high in salt, Processed foods, Foods containing artificial additives. Analyze meal for compliance to plate rule, calculate what is included and what need to be added.\n\n# Steps\n\n1. Analyze the photo to identify the main ingredients of all dishes and estimate their weight.\n2. Combine some of the dishes if they are in the same bowl.\n3. Calculate the total calories and the proportions of proteins, fats, and carbohydrates for the combined dish based on identified ingredients and their weight.\n4. Determine the total weight of the combined dish with gram precision.\n5. Assign a general name in {language} to the combined dish.\n6. Provide a commentary categorizing the dish as healthy or unhealthy:\n   - If healthy, praise the dish.\n   - If unhealthy, offer friendly advice on moderation and provide a gentle overview of potential health consequences. \n   - For plate rule mention use ``` ``` quote. In plate rule mention include score plate compliance with plate rule from 1 to 5 score, where 1 is full uncompliance, 5 - full compliance. If score is not 5, describe what need to be added. Example: ``` Блюдо соответствует правилу тарелки на 1/5. Белки в достаточном количестве, но можно добавить больше овощей. ```\n\n# Output Format\n\nProvide the output in JSON format:\n- `dishes`: a list of objects representing the dishes containing:\n  - `dish_name`: the general name in {language} of the combined dish.\n  - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n  - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n  - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.\n\n# Notes\n\n- Consider possible distortions due to photo quality.\n- Make the best guesses for unidentified ingredients.\n- Include context on general health benefits when applicable."
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

    async def recognize_calories_from_text(self, text: str, language: str) -> list[dict]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Determine the nutritional content (calories, proteins, fats, carbohydrates), ingredients, and weight of combined dishes from a user input. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Unhealthy items include: Foods high in added sugars, Foods high in saturated and trans fats, Foods high in salt, Processed foods, Foods containing artificial additives. Analyze meal for compliance to plate rule, calculate what is included and what need to be added.\n\n# Steps\n\n1. Analyze the photo to identify the main ingredients of all dishes and estimate their weight.\n2. Combine some of the dishes if they are in the same bowl.\n3. Calculate the total calories and the proportions of proteins, fats, and carbohydrates for the combined dish based on identified ingredients and their weight.\n4. Determine the total weight of the combined dish with gram precision.\n5. Assign a general name in {language} to the combined dish.\n6. Provide a commentary categorizing the dish as healthy or unhealthy:\n   - If healthy, praise the dish.\n   - If unhealthy, offer friendly advice on moderation and provide a gentle overview of potential health consequences. \n   - For plate rule mention use ``` ``` quote. In plate rule mention include score plate compliance with plate rule from 1 to 5 score, where 1 is full uncompliance, 5 - full compliance. If score is not 5, describe what need to be added. Example: ``` Блюдо соответствует правилу тарелки на 1/5. Белки в достаточном количестве, но можно добавить больше овощей. ```\n\n# Output Format\n\nProvide the output in JSON format:\n- `dishes`: a list of objects representing the dishes containing:\n  - `dish_name`: the general name in {language} of the combined dish.\n  - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n  - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n  - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.\n\n# Notes\n\n- Consider possible distortions due to photo quality.\n- Make the best guesses for unidentified ingredients.\n- Include context on general health benefits when applicable."
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text
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
#         response = await self.deepseek_client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"Determine the nutritional content (calories, proteins, fats, carbohydrates), ingredients, and weight of combined dishes from a user input. Merge multiple dishes into one unified dish if present in a single photo. Add a general name for the dish and a commentary on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Unhealthy items include: Foods high in added sugars, Foods high in saturated and trans fats, Foods high in salt, Processed foods, Foods containing artificial additives. Analyze meal for compliance to plate rule, calculate what is included and what need to be added.\n\n# Steps\n\n1. Analyze the photo to identify the main ingredients of all dishes and estimate their weight.\n2. Combine some of the dishes if they are in the same bowl.\n3. Calculate the total calories and the proportions of proteins, fats, and carbohydrates for the combined dish based on identified ingredients and their weight.\n4. Determine the total weight of the combined dish with gram precision.\n5. Assign a general name in {language} to the combined dish.\n6. Provide a commentary categorizing the dish as healthy or unhealthy:\n   - If healthy, praise the dish.\n   - If unhealthy, offer friendly advice on moderation and provide a gentle overview of potential health consequences. \n   - For plate rule mention use ``` ``` quote. In plate rule mention include score plate compliance with plate rule from 1 to 5 score, where 1 is full uncompliance, 5 - full compliance. If score is not 5, describe what need to be added. Example: ``` Блюдо соответствует правилу тарелки на 1/5. Белки в достаточном количестве, но можно добавить больше овощей. ```\n\n# Output Format\n\nProvide the output in JSON format:\n- `dishes`: a list of objects representing the dishes containing:\n  - `dish_name`: the general name in {language} of the combined dish.\n  - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n  - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n  - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.\n\n# Notes\n\n- Consider possible distortions due to photo quality.\n- Make the best guesses for unidentified ingredients.\n- Include context on general health benefits when applicable."
#                 },
#                 {"role": "user", "content": text},
#             ],
#             max_tokens=1024,
#             temperature=0.7,
#             response_format={"type": "json_object"},
#             stream=False,
#         )
# 
#         logger.debug(f"Get response: {response}")
#         try:
#             return json.loads(response.choices[0].message.content)
#         except json.JSONDecodeError:
#             return None

    async def recognize_sport_from_text(self, text: str, language: str) -> dict | None:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Identify all sports mentioned in the given text, and specify the duration of each activity and the exact number of calories burned. Compile this information into a JSON structure with very accurate calorie estimations.\n\n# Steps\n\n1. Read the provided text.\n2. Identify all mentioned sports and their duration in seconds. If the duration is given in repetitions, calculate the total exercise time.\n3. For each sport, calculate the number of calories burned in kcal. Ensure that the calculations are very precise.\n4. Populate the JSON structure with the listed attributes for each sport.\n\n# Output Format\n\nPresent the result in a JSON list format with the keys \"comment\" and \"items\", where each element will be a sport object with the following keys:\n- \"name\": Name of the sport in {language} language.\n- \"length\": Duration of the activity in seconds.\n- \"calories\": Number of calories burned with high accuracy.\nComment key contains commentary about identified sport, mention what is provided sport good for and praise user. Use emojis and motivate user.\n\n# Notes\n\n- If the text poses challenges in identifying the sport, consult the context or provided units.\n- Ensure the JSON structure is correctly opened and closed, and all keys contain relevant information.\n- Prioritize accuracy in the calorie calculation, considering detailed factors such as activity intensity and possible provided user characteristics."
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text
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
#         response = await self.deepseek_client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"Identify all sports mentioned in the given text, and specify the duration of each activity and the exact number of calories burned. Compile this information into a JSON structure with very accurate calorie estimations.\n\n# Steps\n\n1. Read the provided text.\n2. Identify all mentioned sports and their duration in seconds. If the duration is given in repetitions, calculate the total exercise time.\n3. For each sport, calculate the number of calories burned in kcal. Ensure that the calculations are very precise.\n4. Populate the JSON structure with the listed attributes for each sport.\n\n# Output Format\n\nPresent the result in a JSON list format with the keys \"comment\" and \"items\", where each element will be a sport object with the following keys:\n- \"name\": Name of the sport in {language} language.\n- \"length\": Duration of the activity in seconds.\n- \"calories\": Number of calories burned with high accuracy.\nComment key contains commentary about identified sport, mention what is provided sport good for and praise user. Use emojis and motivate user.\n\n# Notes\n\n- If the text poses challenges in identifying the sport, consult the context or provided units.\n- Ensure the JSON structure is correctly opened and closed, and all keys contain relevant information.\n- Prioritize accuracy in the calorie calculation, considering detailed factors such as activity intensity and possible provided user characteristics."
#                 },
#                 {"role": "user", "content": text},
#             ],
#             max_tokens=1024,
#             temperature=0.7,
#             response_format={"type": "json_object"},
#             stream=False,
#         )
# 
#         logger.debug(f"Get response: {response}")
#         try:
#             return json.loads(response.choices[0].message.content)
#         except json.JSONDecodeError:
#             return None

    async def edit_meal_text(self, meal_json: str, text: str, language: str) -> list[dict]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f'JSON format:\n- `dishes`: a list of objects representing the dishes containing:\n  - `dish_name`: the general name in {language} of the combined dish.\n  - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n  - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n  - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.' \
                                    f'Modify the nutritional values (calories, proteins, fats, and carbohydrates) and the dish or ingredient composition and a commentary in {language} language on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Update is based on user input within a JSON structure.\n\nReceive a JSON structure containing nutritional information for a dish and its ingredients. Accept user input to specify changes, which may include adding, removing, or replacing entire dishes or specific ingredients, along with recalculating their nutritional values. Implement these changes while ensuring the data remains correctly formatted.\n\n# Steps\n\n1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.\n2. Receive input from the user specifying changes, which may involve:\n   - Altering nutritional values with gram precision (e.g., calories, proteins) for existing items.\n   - Adding new dishes or ingredients with calculated nutritional values.\n   - Removing existing dishes or ingredients.\n   - Replacing existing dishes or ingredients with new ones.\n3. Apply the specified changes to the corresponding fields in the JSON data.\n4. Recalculate the total nutritional values with gram precision (calories, proteins, fats, and carbohydrates) to ensure consistency.\n5. Rewrite "commentary" field for new dishes, use emojis.\n6. Ensure that all data remains in the correct format.\n\n# Output Format\n\nReturn the updated data in JSON format without using code blocks.\n\n# Notes\n\n- Ensure that changes match the user\'s request exactly',
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "JSON data: " + meal_json
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "User input: " + text
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
#         response = await self.deepseek_client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f'JSON format:\n- `dishes`: a list of objects representing the dishes containing:\n  - `dish_name`: the general name in {language} of the combined dish.\n  - `ingredients`: a list of objects in {language} for each identified ingredient and its weight with gram precision to `ingredient` and `weight` fields.\n  - `nutrition`: an object with fields `calories`, `protein`, `fats`, `carbohydrates` calculated with gram precision.\n  - `weight`: the total weight of the combined dish with gram precision.\n- `commentary`: a string with categorizing remarks of the combined dish. Use varied text and emojis.' \
        #                             f'Modify the nutritional values (calories, proteins, fats, and carbohydrates) and the dish or ingredient composition and a commentary in {language} language on the category of the dish as either healthy or unhealthy. Praise the dish if it is healthy, or offer friendly advice on moderation if it is unhealthy. Update is based on user input within a JSON structure.\n\nReceive a JSON structure containing nutritional information for a dish and its ingredients. Accept user input to specify changes, which may include adding, removing, or replacing entire dishes or specific ingredients, along with recalculating their nutritional values. Implement these changes while ensuring the data remains correctly formatted.\n\n# Steps\n\n1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.\n2. Receive input from the user specifying changes, which may involve:\n   - Altering nutritional values with gram precision (e.g., calories, proteins) for existing items.\n   - Adding new dishes or ingredients with calculated nutritional values.\n   - Removing existing dishes or ingredients.\n   - Replacing existing dishes or ingredients with new ones.\n3. Apply the specified changes to the corresponding fields in the JSON data.\n4. Recalculate the total nutritional values with gram precision (calories, proteins, fats, and carbohydrates) to ensure consistency.\n5. Rewrite "commentary" field for new dishes, use emojis.\n6. Ensure that all data remains in the correct format.\n\n# Output Format\n\nReturn the updated data in JSON format without using code blocks.\n\n# Notes\n\n- Ensure that changes match the user\'s request exactly',
#                 },
#                 {"role": "user", "content": "JSON data: " + meal_json},
#                 {"role": "user", "content": "User input: " + text},
#             ],
#             max_tokens=2048,
#             temperature=0.7,
#             response_format={"type": "json_object"},
#             stream=False,
#         )
# 
#         logger.debug(f"Get response: {response}")
#         try:
#             return json.loads(response.choices[0].message.content)
#         except json.JSONDecodeError:
#             return None

    async def edit_sport_text(self, sport_json: str, text: str, language: str) -> list[dict]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": f"JSON format:\n- `items`: a list of objects representing the sports containing:\n  - `name`: the general name in {language} of the sport.\n  - `length`: duration in seconds of the sport.\n  - `calories`: the total calories of the sport.\n\nModify the calories values or sports composition. Update is based on user input within a JSON structure.\n\nReceive a JSON structure containing calories information for a sport. Accept user input to specify changes, which may include adding, removing, or replacing entire sport, along with recalculating their calories values. Implement these changes while ensuring the data remains correctly formatted.\n\n# Steps\n\n1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.\n2. Receive input from the user specifying changes, which may involve:\n   - Altering calories values with gram precision for existing items.\n   - Adding new sports with calculated nutritional values.\n   - Removing existing sports.\n   - Replacing existing sports with new ones.\n3. Apply the specified changes to the corresponding fields in the JSON data.\n4. Recalculate the total calories values with gram precision to ensure consistency.\n5. Ensure that all data remains in the correct format.\n\n# Output Format\n\nReturn the updated data in JSON format without using code blocks.\n\n# Notes\n\n- Ensure that changes match the user's request exactly."
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "JSON data: " + sport_json
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "User input: " + text
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
#         response = await self.deepseek_client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"JSON format:\n- `items`: a list of objects representing the sports containing:\n  - `name`: the general name in {language} of the sport.\n  - `length`: duration in seconds of the sport.\n  - `calories`: the total calories of the sport.\n\nModify the calories values or sports composition. Update is based on user input within a JSON structure.\n\nReceive a JSON structure containing calories information for a sport. Accept user input to specify changes, which may include adding, removing, or replacing entire sport, along with recalculating their calories values. Implement these changes while ensuring the data remains correctly formatted.\n\n# Steps\n\n1. Obtain the JSON structure containing the nutritional information for the dish and its ingredients.\n2. Receive input from the user specifying changes, which may involve:\n   - Altering calories values with gram precision for existing items.\n   - Adding new sports with calculated nutritional values.\n   - Removing existing sports.\n   - Replacing existing sports with new ones.\n3. Apply the specified changes to the corresponding fields in the JSON data.\n4. Recalculate the total calories values with gram precision to ensure consistency.\n5. Ensure that all data remains in the correct format.\n\n# Output Format\n\nReturn the updated data in JSON format without using code blocks.\n\n# Notes\n\n- Ensure that changes match the user's request exactly."
#                 },
#                 {"role": "user", "content": "JSON data: " + sport_json},
#                 {"role": "user", "content": "User input: " + text},
#             ],
#             max_tokens=2048,
#             temperature=0.7,
#             response_format={"type": "json_object"},
#             stream=False,
#         )
# 
#         logger.debug(f"Get response: {response}")
#         try:
#             return json.loads(response.choices[0].message.content)
#         except json.JSONDecodeError:
#             return None
