from uuid import UUID

from src.user.application.interfaces.user_uow import IUserUnitOfWork


class DeleteUserUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> None:
        async with self.uow:
            await self.uow.users.delete_by_pk(user_id)
            await self.uow.commit()

