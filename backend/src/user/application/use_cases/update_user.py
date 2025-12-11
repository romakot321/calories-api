from uuid import UUID

from src.user.domain.dtos import UserReadDTO, UserUpdateDTO
from src.user.domain.entities import User, UserUpdate
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class UpdateUserUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID, dto: UserUpdateDTO) -> UserReadDTO:
        user = UserUpdate(**dto.model_dump(exclude_unset=True))
        async with self.uow:
            user = await self.uow.users.update_by_pk(user_id, user)
            await self.uow.commit()
        return UserReadDTO(**user.model_dump())
