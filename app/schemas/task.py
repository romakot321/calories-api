from pydantic import BaseModel, ConfigDict, Field, computed_field
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
        def total_kilocalories(self) -> int | None:
            return self.weight * self.kilocalories_per100g if self.weight else None

    id: UUID
    error: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)


class TaskAudioSchema(BaseModel):
    class Item(BaseModel):
        sport: str | None = Field(default=None, validation_alias="product")
        kilocalories_per1h: int | None = Field(default=None, validation_alias="kilocalories_per100g")
        time: int | None = Field(default=None, validation_alias="weight")

        @computed_field
        @property
        def total_kilocalories(self) -> int | None:
            return self.time * self.kilocalories_per1h if self.time else None

    id: UUID
    error: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)

