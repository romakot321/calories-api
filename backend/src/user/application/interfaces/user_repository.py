import abc
from uuid import UUID

from src.user.domain.entities import User, UserFilters, UserUpdate


class IUserRepository(abc.ABC):
    @abc.abstractmethod
    async def create(self, data: User) -> User: ...

    @abc.abstractmethod
    async def get_by_pk(self, pk: UUID) -> User: ...

    @abc.abstractmethod
    async def get_by_apphud_id(self, apphud_id: str) -> User: ...

    @abc.abstractmethod
    async def get_by_filters(self, filters: UserFilters) -> list[User]: ...

    @abc.abstractmethod
    async def update_by_pk(self, pk: UUID, data: UserUpdate) -> User: ...

    @abc.abstractmethod
    async def delete_by_pk(self, pk: UUID) -> None: ...
