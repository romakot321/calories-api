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
                    "text": "Analyze the provided food photo and return nutritional information. Use this JSON structure:\n\n{\n  \"items\": [\n    {\n      \"product\": \"identified_food_name\",\n      \"weight\": estimated_weight_in_grams,\n      \"kilocalories_per100g\": int,\n      \"proteins_per100g\": int,\n      \"fats_per100g\": int,\n      \"carbohydrates_per100g\": int,\n      \"fiber_per100g\": int,\n      \"confidence\": \"high/medium/low\"\n    }\n  ],\n  \"total_kilocalories\": sum_of_all_items_kcal,\n  \"error\": null | \"brief_error_message\"\n}\n\nGuidelines:\n1. Estimate weight and nutritional values per 100g\n2. Calculate total kcal: (kilocalories_per100g * weight / 100)\n3. Include confidence for identification accuracy\n4. Return error if food unclear\n5. Only JSON output, no explanations"
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
            temperature=0.7,
            max_completion_tokens=4000,
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

