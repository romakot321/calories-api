from pydantic import BaseModel, ConfigDict, Field, computed_field
from uuid import UUID


class TaskSchema(BaseModel):
    class Item(BaseModel):
        product: str | None = None
        weight: float | None = None
        kilocalories_per100g: float | None = None
        proteins_per100g: float | None = None
        fats_per100g: float | None = None
        carbohydrates_per100g: float | None = None
        fiber_per100g: float | None = None
        action: str | None = None

        @computed_field
        @property
        def total_kilocalories(self) -> float:
            return (
                self.weight * self.kilocalories_per100g / 100
                if self.kilocalories_per100g
                else None
            )

        model_config = ConfigDict(from_attributes=True)

    id: UUID
    error: str | None = None
    text: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)


class TaskAudioSchema(BaseModel):
    class Item(BaseModel):
        sport: str | None = Field(default=None, validation_alias="product")
        kilocalories_per1h: float | None = Field(
            default=None, validation_alias="kilocalories_per100g"
        )
        time: float | None = Field(default=None, validation_alias="weight")
        action: str | None = None

        @computed_field
        @property
        def total_kilocalories(self) -> float | None:
            return self.time * (self.kilocalories_per1h / 3600) if self.time else None

    id: UUID
    error: str | None = None
    text: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)


class TaskTextCreateSchema(BaseModel):
    text: str
