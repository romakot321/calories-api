from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import async_session_maker
from src.user.infrastructure.repository import UserRepository
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class UserUnitOfWork(IUserUnitOfWork):
    def __init__(self, session_factory=async_session_maker) -> None:
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session: AsyncSession = self.session_factory()
        self.users = UserRepository(self.session)
        return await super().__aenter__()

    async def commit(self) -> None:
        await self.session.commit()

    async def _rollback(self) -> None:
        await self.session.rollback()

