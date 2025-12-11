from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError, MissingGreenlet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.exceptions import DBModelConflictException, DBModelNotFoundException
from src.task.domain.entities import (
    Task,
    TaskCreate,
    TaskProduct,
    TaskProductIngredient,
    TaskSport,
    TaskStatus,
    TaskUpdate,
)
from src.task.infrastructure.db.orm import TaskDB, TaskProductDB, TaskProductIngredientDB, TaskSportDB
from src.task.application.interfaces.task_repository import ITaskRepository


class PGTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _flush(self):
        try:
            await self.session.flush()
        except IntegrityError as e:
            detail = "Model can't be created. " + str(e)
            raise DBModelConflictException(detail) from e

    async def create(self, data: TaskCreate) -> Task:
        model = TaskDB(**(data.model_dump() | {"status": "queued"}))
        self.session.add(model)
        await self._flush()
        return self._to_domain(model)

    async def get_by_pk(self, pk: UUID) -> Task:
        model = await self.session.get(
            TaskDB,
            pk,
            options=[
                selectinload(TaskDB.products).selectinload(TaskProductDB.ingredients),
                selectinload(TaskDB.sports),
            ],
        )
        if model is None:
            raise DBModelNotFoundException()
        return self._to_domain(model)

    async def update_by_pk(self, pk: UUID, data: TaskUpdate) -> Task:
        query = update(TaskDB).filter_by(id=pk).values(**data.model_dump(mode="json", exclude_none=True))
        await self.session.execute(query)

        if data.products:
            await self.session.execute(delete(TaskProductDB).filter_by(task_id=pk))
            self.session.add_all(
                [
                    TaskProductDB(
                        **product.model_dump(mode="json", exclude={"ingredients"}),
                        ingredients=[
                            TaskProductIngredientDB(**ing.model_dump(mode="json")) for ing in product.ingredients
                        ],
                    )
                    for product in data.products
                ]
            )
        if data.sports:
            await self.session.execute(delete(TaskSportDB).filter_by(task_id=pk))
            self.session.add_all(
                [
                    TaskSportDB(
                        **sport.model_dump(mode="json"),
                    )
                    for sport in data.sports
                ]
            )

        await self._flush()
        return await self.get_by_pk(pk)

    @staticmethod
    def _to_domain(model: TaskDB) -> Task:
        try:
            products = [
                TaskProduct(
                    name=product.name,
                    weight=product.weight,
                    calories=product.calories,
                    proteins=product.proteins,
                    fiber=product.fiber,
                    carbohydrates=product.carbohydrates,
                    fats=product.fats,
                    ingredients=[
                        TaskProductIngredient(
                            name=ing.name,
                            weight=ing.weight,
                            calories=ing.kilocalories,
                            proteins=ing.proteins,
                            fiber=ing.fiber,
                            carbohydrates=ing.carbohydrates,
                            fats=ing.fats,
                        )
                        for ing in product.ingredients
                    ],
                )
                for product in model.products
            ]
        except MissingGreenlet:
            products = []

        try:
            sports = [
                TaskSport(name=sport.name, calories=sport.calories, length=sport.length) for sport in model.sports
            ]
        except MissingGreenlet:
            sports = []

        return Task(
            id=model.id,
            user_id=model.user_id,
            app_bundle=model.app_bundle,
            status=TaskStatus(model.status),
            error=model.error,
            request_text=model.request_text,
            request_filename=model.request_filename,
            products=products,
            sports=sports,
        )
