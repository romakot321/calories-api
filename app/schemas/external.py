from pydantic import BaseModel


class ExternalResponseSchema(BaseModel):
    class Item(BaseModel):
        class NutritionalInfo(BaseModel):
            class Nutrition(BaseModel):
                class Info(BaseModel):
                    label: str
                    quantity: float
                    unit: str

                ALC: Info
                CHOCDF: Info
                ENERC_KCAL: Info
                FAT: Info
                FIBTG: Info
                PROCNT: Info

            calories: float
            totalNutrients: Nutrition

        food_item_position: int
        nutritional_info: NutritionalInfo
        serving_size: float  # In grams

    foodName: list[str]
    nutritional_info_per_item: list[Item]


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

