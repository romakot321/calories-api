import inspect
from uuid import UUID
from typing import Type, TypeVar

from fastapi import Form
from pydantic import Field, HttpUrl, BaseModel

from src.task.domain.entities import TaskStatus
from src.integration.domain.dtos import IntegrationTaskRunParamsDTO

_T = TypeVar("_T", bound=BaseModel)


def as_form(cls: type[_T]) -> type[_T]:
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        new_parameters.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=Form(...) if model_field.is_required() else Form(model_field.default),
                annotation=model_field.annotation,
            )
        )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    cls.as_form = as_form_func  # type: ignore
    return cls


@as_form
class TaskCreateDTO(IntegrationTaskRunParamsDTO, BaseModel):
    app_bundle: str
    webhook_url: HttpUrl | None = None


@as_form
class TaskCreateWithTextDTO(IntegrationTaskRunParamsDTO, BaseModel):
    app_bundle: str
    text: str
    webhook_url: HttpUrl | None = None


class TaskProductIngredientDTO(BaseModel):
    name: str | None = None
    weight: float | None = None
    kilocalories_per100g: float | None = None
    proteins_per100g: float | None = Field(None, description="Клетчатка")
    fats_per100g: float | None = None
    carbohydrates_per100g: float | None = None
    fiber_per100g: float | None = Field(None, description="Белки")


class TaskProductDTO(BaseModel):
    name: str | None = None
    weight: float | None = None
    kilocalories_per100g: float | None = None
    proteins_per100g: float | None = Field(None, description="Клетчатка")
    fats_per100g: float | None = None
    carbohydrates_per100g: float | None = None
    fiber_per100g: float | None = Field(None, description="Белки")

    ingredients: list[TaskProductIngredientDTO]


class TaskSportDTO(BaseModel):
    name: str | None = None
    calories: float | None = None
    length: int | None = None


class TaskReadDTO(BaseModel):
    id: UUID
    status: TaskStatus
    products: list[TaskProductDTO]
    sports: list[TaskSportDTO]
    error: str | None = None


class TaskResultDTO(BaseModel):
    status: TaskStatus
    external_task_id: str | None = None
    products: list[TaskProductDTO]
    sports: list[TaskSportDTO]
    error: str | None = None
