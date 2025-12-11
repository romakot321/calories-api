from uuid import uuid4
from fastapi import HTTPException

from src.db.exceptions import DBModelConflictException, DBModelNotFoundException
from src.user.domain.dtos import UserReadDTO, UserCreateDTO
from src.user.domain.entities import User
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class CreateUserUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: UserCreateDTO) -> UserReadDTO:
        user = User(id=uuid4(), **dto.model_dump())
        async with self.uow:
            try:
                user = await self.uow.users.get_by_apphud_id(dto.apphud_id)
            except DBModelNotFoundException:
                user = await self.uow.users.create(user)
                await self.uow.commit()
            except DBModelConflictException as e:
                raise HTTPException(409) from e
            await self.uow.commit()
        return UserReadDTO(**user.model_dump())
