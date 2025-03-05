import os

import aiohttp


class TranslateRepository:
    YANDEX_CLOUD_TOKEN = os.getenv("YANDEX_CLOUD_TOKEN")
    YANDEX_CLOUD_FOLDER_ID = os.getenv("YANDEX_CLOUD_FOLDER_ID")

    async def translate_from_en_to_ru(self, *texts: str) -> list[str]:
        body = {
            "targetLanguageCode": "ru",
            "texts": texts,
            "folderId": self.YANDEX_CLOUD_FOLDER_ID,
            "sourceLanguageCode": "en"
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Api-Key {0}".format(self.YANDEX_CLOUD_TOKEN),
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                "https://translate.api.cloud.yandex.net/translate/v2/translate",
                json=body,
                headers=headers,
            )
            assert resp.status == 200, await resp.text()
            resp_body = await resp.json()
            return list(map(lambda i: i["text"], resp_body["translations"]))
