from pydantic import BaseModel, ConfigDict, computed_field
from uuid import UUID


class TaskSchema(BaseModel):
    class Item(BaseModel):
        product: str | None = None
        weight: int | None = None
        kilocalories_per100g: int | None = None
        proteins_per100g: int | None = None
        fats_per100g: int | None = None
        carbohydrates_per100g: int | None = None
        fiber_per100g: int | None = None

        @computed_field
        @property
        def total_kilocalories(self) -> int:
            return self.weight * self.kilocalories_per100g // 100 if self.weight else None

        model_config = ConfigDict(from_attributes=True)

    id: UUID
    error: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)

