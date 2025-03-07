from pydantic import BaseModel


class MealDBProduct(BaseModel):
    product: str
    weight: float
    action: str
    fats: float
    carbohydrates: float
    fiber: float
    calories: float
