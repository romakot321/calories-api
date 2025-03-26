from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, computed_field, Json
from uuid import UUID


class TaskSchema(BaseModel):
    class Item(BaseModel):
        """Ingredients field is a json list with keys {ingredient: str, weight: int}"""
        product: str | None = None
        weight: float | None = None
        kilocalories_per100g: float | None = None
        fats_per100g: float | None = None
        carbohydrates_per100g: float | None = None
        fiber_per100g: float | None = None
        ingredients: list[dict] | None = None
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
    comment: str | None = None
    text: str | None = None
    items: list[Item]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories if i.total_kilocalories is not None else 0, self.items))

    model_config = ConfigDict(from_attributes=True)


class TaskSportSchema(BaseModel):
    class SportItem(BaseModel):
        sport: str | None = Field(default=None, validation_alias="product")
        total_kilocalories: float | None = Field(
            default=None, validation_alias="kilocalories_per100g"
        )
        time: float | None = Field(default=None, validation_alias="weight")

    id: UUID
    error: str | None = None
    text: str | None = None
    comment: str | None = None
    items: list[SportItem]

    @computed_field
    @property
    def total_kilocalories(self) -> int:
        return sum(map(lambda i: i.total_kilocalories, self.items))

    model_config = ConfigDict(from_attributes=True)


class Language(Enum):
    russian = "Russian"
    english = "english"


class TaskTextCreateSchema(BaseModel):
    text: str
    language: Language = Language.russian


class TaskEditSchema(BaseModel):
    user_input: str
    language: Language = Language.russian


class TaskConsultationCreateSchema(BaseModel):
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


class TaskConsultationSchema(BaseModel):
    text: str
