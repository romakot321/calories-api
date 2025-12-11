from enum import Enum
from typing import Literal

from pydantic import BaseModel


class IntegrationTaskStatus(str, Enum):
    queued = "queued"
    started = "started"
    finished = "finished"
    failed = "failed"


class IntegrationTaskRunParamsDTO(BaseModel):
    language: Literal["russian", "english"]


class IntegrationTaskResultDTO(BaseModel):
    status: IntegrationTaskStatus
    external_task_id: str | None = None
    result: list[dict] | None = None
    error: str | None = None
