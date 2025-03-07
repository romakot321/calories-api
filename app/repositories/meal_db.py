import asyncio
import os
import json
import aiomysql
from contextlib import asynccontextmanager
from fastapi import Depends
from loguru import logger

from app.schemas.meal_db import MealDBProduct

nutritions_table = {
    '1': "fats",
    '8': "carbohydrates",
    '14': "fiber"
}

pool = None


@asynccontextmanager
async def get_session():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            logger.debug("OPENED")
            yield cur
            logger.debug("CLOSED")


class MealDBRepository:
    def __init__(self, session=Depends(get_session)):
        self.session = session

    async def search_product(self, name: str, weight: int, action: str) -> MealDBProduct | None:
        async with self.session as session:
            await session.execute(f"SELECT * FROM products WHERE title LIKE '%{name}%';")
            row = await session.fetchone()
        if row is None:
            return
        id, title, kcal, nutritions = row[0], row[1], row[14], row[17]
        nutritions = json.loads(nutritions)
        return MealDBProduct(
            product=name,
            weight=weight,
            action=action,
            fats=float(nutritions['1']) if nutritions.get('1') is not None else 0,
            carbohydrates=float(nutritions['8']) if nutritions.get('8') is not None else 0,
            fiber=float(nutritions['14']) if nutritions.get('14') is not None else 0,
            calories=float(kcal)
        )

    @classmethod
    async def init_database_pool(cls):
        global pool
        pool = await aiomysql.create_pool(
            user=os.getenv("MEAL_DB_USER"),
            db=os.getenv("MEAL_DB_DB"),
            host=os.getenv("MEAL_DB_HOST"),
            password=os.getenv("MEAL_DB_PASSWORD"),
        )
