import abc

from src.user.application.interfaces.user_repository import IUserRepository


class IUserUnitOfWork(abc.ABC):
    users: IUserRepository

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._rollback()

    @abc.abstractmethod
    async def commit(self): ...

    @abc.abstractmethod
    async def _rollback(self): ...
