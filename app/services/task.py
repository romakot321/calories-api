from typing import BinaryIO
from fastapi import Depends, UploadFile
from loguru import logger
from uuid import UUID
import io
import pydantic

from app.repositories.meal_db import MealDBRepository
from app.repositories.task import TaskRepository
from app.repositories.external import ExternalRepository
from app.repositories.translate import TranslateRepository
from app.schemas.meal_db import MealDBProduct
from app.schemas.task import Language, TaskEditSchema, TaskSchema, TaskSportSchema, TaskTextCreateSchema
from app.schemas.external import (
    ExternalAudioMealResponseSchema,
    ExternalAudioSportResponseSchema,
    ExternalResponseSchema,
)
from app.db.tables import Task, TaskItem


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository = Depends(),
        translate_repository: TranslateRepository = Depends(),
        external_repository: ExternalRepository = Depends(),
        mealdb_repository: MealDBRepository = Depends(),
    ):
        self.task_repository = task_repository
        self.external_repository = external_repository
        self.translate_repository = translate_repository
        self.mealdb_repository = mealdb_repository

    async def create(self) -> TaskSchema:
        model = await self.task_repository.create(Task())
        return TaskSchema.model_validate(model)

    async def send(self, task_id: UUID, file_raw: bytes, language: Language):
        response = await self.external_repository.send(file_raw, language.value)
        try:
            response = ExternalResponseSchema.model_validate(response)
        except pydantic.ValidationError as e:
            logger.debug("Invalid external image response get")
            logger.exception(e)
            await self.task_repository.update(task_id, error="Invalid input image")
            return

        logger.debug("External image response: " + str(response.model_dump()))
        items = [
            TaskItem(
                product=item.dish_name,
                kilocalories_per100g=item.nutrition.calories / item.weight * 100,
                fiber_per100g=item.nutrition.protein / item.weight * 100,
                fats_per100g=item.nutrition.fats / item.weight * 100,
                carbohydrates_per100g=item.nutrition.carbohydrates / item.weight * 100,
                weight=item.weight,
                ingredients=item.model_dump()["ingredients"],
                task_id=task_id,
            )
            for item in response.dishes
        ]
        await self.task_repository.update(task_id, comment=response.commentary)
        await self.task_repository.create_items(*items)

    async def send_audio(self, task_id: UUID, file_raw: bytes, language: Language):
        buffer = io.BytesIO(file_raw)
        buffer.name = "tmp.mp3"
        response = await self.external_repository.send_audio(buffer)
        if response is None:
            await self.task_repository.update(task_id, error="Invalid input audio")
            return
        await self.send_text(
            task_id, TaskTextCreateSchema(text=response["text"], language=language)
        )

    async def send_sport_audio(self, task_id: UUID, file_raw: bytes, language: Language):
        buffer = io.BytesIO(file_raw)
        buffer.name = "tmp.mp3"
        response = await self.external_repository.send_audio(buffer)
        if response is None:
            await self.task_repository.update(task_id, error="Invalid input audio")
            return
        await self.send_text_sport(
            task_id, TaskTextCreateSchema(text=response["text"], language=language)
        )

    async def send_text(self, task_id: UUID, schema: TaskTextCreateSchema):
        await self.task_repository.update(task_id, text=schema.text)
        try:
            response = await self.external_repository.recognize_calories_from_text(
                schema.text, schema.language.value
            )
        except Exception as e:
            logger.exception(e)
            await self.task_repository.update(task_id, error="Internal error")
            return
        try:
            response = ExternalResponseSchema.model_validate(response)
        except pydantic.ValidationError as e:
            logger.error("Invalid external text response get")
            logger.exception(e)
            await self.task_repository.update(task_id, error="Invalid input image")
            return
        items = [
            TaskItem(
                product=item.dish_name,
                kilocalories_per100g=item.nutrition.calories / item.weight * 100,
                fiber_per100g=item.nutrition.protein / item.weight * 100,
                fats_per100g=item.nutrition.fats / item.weight * 100,
                carbohydrates_per100g=item.nutrition.carbohydrates / item.weight * 100,
                weight=item.weight,
                ingredients=item.model_dump()["ingredients"],
                task_id=task_id,
            )
            for item in response.dishes
        ]
        await self.task_repository.update(task_id, comment=response.commentary)
        await self.task_repository.create_items(*items)

    async def send_text_sport(self, task_id: UUID, schema: TaskTextCreateSchema):
        await self.task_repository.update(task_id, text=schema.text)
        response = await self.external_repository.recognize_sport_from_text(
            schema.text, schema.language.value
        )
        try:
            response = ExternalAudioSportResponseSchema.model_validate(response)
        except pydantic.ValidationError as e:
            logger.debug("Invalid external text response get")
            logger.exception(e)
            await self.task_repository.update(task_id, error="Invalid input text")
            return
        items = [
            TaskItem(
                product=i.name,
                weight=i.length,
                kilocalories_per100g=i.total_kilocalories,
                task_id=task_id,
            )
            for i in response.items
        ]
        await self.task_repository.create_items(*items)

    async def get(self, task_id: UUID) -> Task:
        return await self.task_repository.get(task_id)

    async def send_edit(
        self, old_task_id: UUID, new_task_id: UUID, schema: TaskEditSchema
    ):
        """Get task, edit data and create new task with updated fields"""
        model = await self.task_repository.get(old_task_id)
        model_schema = TaskSchema.model_validate(model)
        response = await self.external_repository.edit_meal_text(
            model_schema.model_dump_json(), schema.user_input, schema.language.value
        )

        try:
            response = TaskSchema.model_validate(response)
        except pydantic.ValidationError as e:
            logger.debug("Invalid external text response get")
            logger.exception(e)
            await self.task_repository.update(new_task_id, error="Invalid input text")
            return

        items = [
            TaskItem(**i.model_dump(exclude="total_kilocalories"), task_id=new_task_id)
            for i in response.items
        ]
        await self.task_repository.create_items(*items)
        await self.task_repository.update(new_task_id, comment=response.comment)

    async def send_edit_sport(
        self, old_task_id: UUID, new_task_id: UUID, schema: TaskEditSchema
    ):
        """Get task, edit data and create new task with updated fields"""
        model = await self.task_repository.get(old_task_id)
        model_schema = TaskSportSchema.model_validate(model)
        response = await self.external_repository.edit_sport_text(
            model_schema.model_dump_json(), schema.user_input, schema.language.value
        )

        try:
            response = TaskSportSchema.model_validate(response)
        except pydantic.ValidationError as e:
            logger.debug("Invalid external text response get")
            logger.exception(e)
            await self.task_repository.update(new_task_id, error="Invalid input text")
            return

        items = [
            TaskItem(
                product=i.sport,
                weight=i.time,
                kilocalories_per100g=i.total_kilocalories,
                task_id=new_task_id,
            )
            for i in response.items
        ]
        await self.task_repository.create_items(*items)
