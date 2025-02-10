from fastapi import Depends, UploadFile
from loguru import logger
from uuid import UUID

import pydantic

from app.repositories.task import TaskRepository
from app.repositories.external import ExternalRepository
from app.schemas.task import TaskSchema
from app.schemas.external import ExternalResponseSchema
from app.db.tables import Task


class TaskService:
    def __init__(
            self,
            task_repository: TaskRepository = Depends(),
            external_repository: ExternalRepository = Depends()
    ):
        self.task_repository = task_repository
        self.external_repository = external_repository

    async def create(self) -> TaskSchema:
        model = await self.task_repository.create(Task())
        return TaskSchema.model_validate(model)

    async def send(self, task_id: UUID, file_raw: bytes):
        response = await self.external_repository.send(file_raw)
        try:
            response = ExternalResponseSchema.model_validate(response)
        except pydantic.ValidationError:
            logger.debug("Invalid external response get")
            await self.task_repository.update(task_id, error="Invalid input image")
            return
        logger.debug("External response: " + str(response.model_dump()))
        await self.task_repository.update(task_id, **response.model_dump())

    async def get(self, task_id: UUID) -> TaskSchema:
        model = await self.task_repository.get(task_id)
        return TaskSchema.model_validate(model)

