from pydantic import BaseModel, Field, AliasChoices


class ExternalResponseSchema(BaseModel):
    class Dish(BaseModel):
        class Ingredient(BaseModel):
            ingredient: str
            weight: float

        class Nutrition(BaseModel):
            calories: float
            protein: float
            fats: float
            carbohydrates: float

        dish_name: str
        ingredients: list[Ingredient]
        nutrition: Nutrition
        weight: float

    dishes: list[Dish]
    commentary: str = Field(validation_alias=AliasChoices("commentary", "comment"))


class ExternalAudioSportResponseSchema(BaseModel):
    class Item(BaseModel):
        name: str
        length: float
        calories: float

    items: list[Item]
    comment: str


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


class ExternalConsultationSchema(BaseModel):
    class UserData(BaseModel):
        name: str | None
        gender: str | None
        workout_coefficient: float | None
        weight: int | None
        height: int | None
        age: int | None
        target_weight: int | None
        increase_coefficient: float | None

    prompt: str
    user_data: UserData | None = None

