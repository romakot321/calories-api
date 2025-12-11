from io import BytesIO
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.integration.domain.dtos import IntegrationTaskRunParamsDTO


class TaskStatus(str, Enum):
    queued = "queued"
    started = "started"
    failed = "failed"
    finished = "finished"


class TaskProductIngredient(BaseModel):
    name: str | None = None
    weight: float | None = None
    calories: float | None = None
    proteins: float | None = None
    fats: float | None = None
    carbohydrates: float | None = None
    fiber: float | None = None


class TaskProduct(BaseModel):
    name: str | None = None
    weight: float | None = None
    calories: float | None = None
    proteins: float | None = None
    fats: float | None = None
    carbohydrates: float | None = None
    fiber: float | None = None
    commentary: str | None = None

    ingredients: list[TaskProductIngredient]


class TaskSport(BaseModel):
    name: str | None = None
    calories: float | None = None
    length: int | None = None


class Task(BaseModel):
    id: UUID
    user_id: UUID
    app_bundle: str
    status: TaskStatus
    error: str | None = None

    products: list[TaskProduct]
    sports: list[TaskSport]


class TaskCreate(BaseModel):
    user_id: UUID
    app_bundle: str
    request_text: str | None = None
    request_filename: str | None = None
    status: TaskStatus = TaskStatus.queued


class TaskRun(IntegrationTaskRunParamsDTO, BaseModel):
    file: BytesIO | None = None
    text: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    error: str | None = None
    products: list[TaskProduct] | None = None
    sports: list[TaskSport] | None = None
