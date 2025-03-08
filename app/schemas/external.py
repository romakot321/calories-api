from pydantic import BaseModel


class ExternalResponseSchema(BaseModel):
    class Dish(BaseModel):
        class Ingredient(BaseModel):
            ingredient: str
            weight: int

        class Nutrition(BaseModel):
            calories: int
            protein: int
            fats: int
            carbohydrates: int

        dish_name: str
        ingredients: list[Ingredient]
        nutrition: Nutrition
        weight: int

    dishes: list[Dish]
    commentary: str


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

