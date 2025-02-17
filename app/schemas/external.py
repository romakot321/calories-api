from pydantic import BaseModel


class ExternalResponseSchema(BaseModel):
    class Item(BaseModel):
        product: str
        weight: int
        kilocalories_per100g: int
        proteins_per100g: int
        fats_per100g: int
        carbohydrates_per100g: int
        fiber_per100g: int

    items: list[Item]
    total_kilocalories: int
    error: str | None = None


