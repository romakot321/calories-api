from pydantic import BaseModel, ConfigDict
from uuid import UUID


class TaskSchema(BaseModel):
    id: UUID
    product: str | None = None
    weight: int | None = None
    kilocalories_per100g: int | None = None
    proteins_per100g: int | None = None
    fats_per100g: int | None = None
    carbohydrates_per100g: int | None = None
    fiber_per100g: int | None = None

    model_config = ConfigDict(from_attributes=True)

