from uuid import UUID

from fastapi import HTTPException

from src.db.exceptions import DBModelNotFoundException
from src.user.domain.dtos import UserReadDTO
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class GetUserUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> UserReadDTO:
        async with self.uow:
            try:
                user = await self.uow.users.get_by_pk(user_id)
            except DBModelNotFoundException as e:
                raise HTTPException(404) from e
        return UserReadDTO(**user.model_dump())

