from fastapi import HTTPException

from src.core.auth import JWTManager
from src.db.exceptions import DBModelNotFoundException
from src.user.domain.dtos import TokenResponseDTO, UserAuthorizeDTO
from src.user.application.interfaces.user_uow import IUserUnitOfWork


class AuthorizeUserUseCase:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: UserAuthorizeDTO) -> TokenResponseDTO:
        async with self.uow:
            try:
                user = await self.uow.users.get_by_pk(dto.user_id)
            except DBModelNotFoundException as e:
                raise HTTPException(401) from e
            if not user or user.id is None:
                raise HTTPException(401)

            access_token = JWTManager.create_access_token(dto.user_id)

            return TokenResponseDTO(access_token=access_token)
