from sqlalchemy_service import BaseService as BaseRepository
from uuid import UUID

from app.db.tables import User, UserItem


class UserRepository[Table: User, int](BaseRepository):
    base_table = User

    async def create(self, model: User) -> User:
        self.session.add(model)
        await self._commit()
        self.response.status_code = 201
        return await self.get(model.id)

    async def list(self, page=None, count=None) -> list[User]:
        return list(await self._get_list(page=page, count=count))

    async def get(self, username: str) -> User:
        return await self._get_one(
            username=username
        )

    async def update(self, model_id: UUID, **fields) -> User:
        return await self._update(model_id, **fields)

    async def delete(self, model_id: UUID):
        await self._delete(model_id)

