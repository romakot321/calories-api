from pydantic import BaseModel


class ExternalResponseSchema(BaseModel):
    product: str
    weight: int
    kilocalories_per100g: int
    proteins_per100g: int
    fats_per100g: int
    carbohydrates_per100g: int
    fiber_per100g: int

