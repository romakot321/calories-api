from src.user.domain.dtos import UserReadDTO
from src.user.domain.entities import UserFilters
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class ListUsersUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, filters: UserFilters) -> list[UserReadDTO]:
        async with self.uow:
            users = await self.uow.users.get_by_filters(filters)
        return [UserReadDTO(**user.model_dump()) for user in users]

