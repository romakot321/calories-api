from pydantic import BaseModel


class ExternalResponseSchema(BaseModel):
    class Item(BaseModel):
        product: str
        weight: float
        kilocalories_per100g: float
        proteins_per100g: float
        fats_per100g: float
        carbohydrates_per100g: float
        fiber_per100g: float

    items: list[Item]
    total_kilocalories: float
    error: str | None = None



class ExternalAudioSportResponseSchema(BaseModel):
    class Item(BaseModel):
        sport: str
        length: float

    items: list[Item]


class ExternalAudioMealResponseSchema(BaseModel):
    class Item(BaseModel):
        product: str
        weight: float
        kilocalories_per100g: float
        proteins_per100g: float
        fats_per100g: float
        carbohydrates_per100g: float
        fiber_per100g: float
        action: str | None = None

    items: list[Item]

