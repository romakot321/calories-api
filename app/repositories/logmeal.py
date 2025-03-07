import os
from aiohttp import ClientSession


class LogmealRepository:
    API_URL = "https://api.logmeal.com"
    API_COMPANY_TOKEN = os.getenv("LOGMEAL_API_COMPANY_TOKEN")

    async def create_user(self, username: str) -> str:
        """Return logmeal APIUser token"""
        async with ClientSession(
            base_url=self.API_URL,
            headers={"Authorization": "Bearer " + self.API_COMPANY_TOKEN},
        ) as session:
            resp = await session.post("/v2/users/signUp", json={"username": username})
            assert resp.status == 201, await resp.text()
            return (await resp.json())["token"]
