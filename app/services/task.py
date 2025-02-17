from typing import BinaryIO
from fastapi import Depends, UploadFile
from loguru import logger
from uuid import UUID

import pydantic

from app.repositories.task import TaskRepository
from app.repositories.external import ExternalRepository
from app.schemas.task import TaskSchema
from app.schemas.external import ExternalAudioResponseSchema, ExternalResponseSchema
from app.db.tables import Task, TaskItem


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
            logger.debug("Invalid external image response get")
            await self.task_repository.update(task_id, error="Invalid input image")
            return
        logger.debug("External image response: " + str(response.model_dump()))
        items = [TaskItem(**i, task_id=task_id) for i in response.model_dump()['items']]
        await self.task_repository.create_items(*items)

    async def send_audio(self, task_id: UUID, file_object: BinaryIO):
        response = await self.external_repository.send_audio(file_object)
        if response is None:
            await self.task_repository.update(task_id, error="Invalid input audio")
            return

        response = await self.external_repository.translate_audio_response(response)

        try:
            response = ExternalAudioResponseSchema.model_validate(response)
        except pydantic.ValidationError:
            logger.debug("Invalid external audio response get")
            await self.task_repository.update(task_id, error="Invalid input audio")
            return
        logger.debug("External audio response: " + str(response.model_dump()))
        items = [TaskItem(product=i.sport, weight=i.length, task_id=task_id) for i in response.items]
        await self.task_repository.create_items(*items)

    async def get(self, task_id: UUID) -> TaskSchema:
        model = await self.task_repository.get(task_id)
        return TaskSchema.model_validate(model)

