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
                    "text": "You are a very useful assistant. Help me with determining the caloric content of my meal\n\nThe photo shows food products for a meal. Determine which products are shown in the photo and return them ONLY as a JSON list, where each list element should contain:\n  * \"product\" - the name of the product in russian language, \n  * \"weight\" - weight in grams, \n  * \"kilocalories_per100g\" - how many calories are contained in this product in 100 grams, \n  * \"proteins_per100g\" - the amount of proteins of this product per 100 grams, \n  * \"fats_per100g\" - the amount of fat per 100 grams of this product, \n  * \"carbohydrates_per100g\" - the amount of carbohydrates per 100 grams of this product, \n  * \"fiber_per100g\" - the amount of fiber per 100 grams of this product. If there is no meal in image, return ERROR. If you cannot define some field, write 0 instead"
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
            temperature=1.0,
            max_completion_tokens=2048,
            top_p=1,
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

