from uuid import UUID

from sqlalchemy import exc, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.exceptions import DBModelConflictException, DBModelNotFoundException
from src.user.domain.entities import User, UserFilters, UserUpdate
from src.user.infrastructure.models import UserDB
from src.user.application.interfaces.user_repository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: User) -> User:
        model = UserDB(**data.model_dump())
        self.session.add(model)
        try:
            await self.session.flush()
        except exc.IntegrityError as e:
            raise DBModelConflictException("Conflict while model creating") from e
        return self._model_to_entity(model)

    async def get_by_pk(self, pk: UUID) -> User:
        result = await self.session.execute(select(UserDB).where(UserDB.id == pk).options(selectinload(UserDB.tasks)))
        model = result.scalar_one_or_none()
        if not model:
            raise DBModelNotFoundException(f"User with id {pk} not found")
        return self._model_to_entity(model)

    async def get_by_apphud_id(self, apphud_id: str) -> User:
        result = await self.session.execute(select(UserDB).where(UserDB.apphud_id == apphud_id))
        model = result.scalar_one_or_none()
        if not model:
            raise DBModelNotFoundException(f"User with apphud_id {apphud_id} not found")
        return self._model_to_entity(model)

    async def get_by_filters(self, filters: UserFilters) -> list[User]:
        query = select(UserDB)
        query = query.offset(filters.offset).limit(filters.count)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def update_by_pk(self, pk: UUID, data: UserUpdate) -> User:
        result = await self.session.execute(select(UserDB).where(UserDB.id == pk))
        model = result.scalar_one_or_none()
        if not model:
            raise DBModelNotFoundException(f"User with id {pk} not found")

        [setattr(model, key, value) for key, value in data.model_dump(exclude_unset=True).items()]

        await self.session.flush()
        return self._model_to_entity(model)

    async def delete_by_pk(self, pk: UUID) -> None:
        await self.session.execute(delete(UserDB).where(UserDB.id == pk))

    def _model_to_entity(self, model: UserDB) -> User:
        if model.gender != "f" and model.gender != "m":
            raise ValueError(f"Invalid user gender {model.gender}")

        return User(
            id=model.id,
            apphud_id=model.apphud_id,
            gender=model.gender,
            age=model.age,
            height=model.height,
            target=model.target,
        )
