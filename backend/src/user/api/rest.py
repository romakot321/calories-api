from uuid import UUID

from fastapi import Depends, APIRouter

from src.core.auth import get_current_user_id
from src.user.application.use_cases.update_user import UpdateUserUseCase
from src.user.domain.dtos import UserReadDTO, UserCreateDTO, TokenResponseDTO, UserAuthorizeDTO, UserUpdateDTO
from src.user.api.dependencies import UserUoWDepend
from src.user.application.use_cases.get_user import GetUserUseCase
from src.user.application.use_cases.create_user import CreateUserUseCase
from src.user.application.use_cases.authorize_user import AuthorizeUserUseCase

router = APIRouter()


@router.post("", response_model=UserReadDTO)
async def create_user(dto: UserCreateDTO, uow: UserUoWDepend):
    return await CreateUserUseCase(uow).execute(dto)


@router.patch("", response_model=UserReadDTO)
async def update_me(dto: UserUpdateDTO, uow: UserUoWDepend, current_user_id: UUID = Depends(get_current_user_id)):
    return await UpdateUserUseCase(uow).execute(current_user_id, dto)


@router.get("/me", response_model=UserReadDTO)
async def get_me(uow: UserUoWDepend, current_user_id: UUID = Depends(get_current_user_id)):
    return await GetUserUseCase(uow).execute(current_user_id)


@router.post("/authorize", response_model=TokenResponseDTO)
async def authorize_user(dto: UserAuthorizeDTO, uow: UserUoWDepend):
    return await AuthorizeUserUseCase(uow).execute(dto)
