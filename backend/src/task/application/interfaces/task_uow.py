import abc

from src.task.application.interfaces.task_repository import ITaskRepository
from src.user.application.interfaces.user_repository import IUserRepository


class ITaskUnitOfWork(abc.ABC):
    tasks: ITaskRepository
    users: IUserRepository

    async def commit(self):
        return await self._commit()

    @abc.abstractmethod
    async def _commit(self): ...

    @abc.abstractmethod
    async def _rollback(self): ...

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self._rollback()
