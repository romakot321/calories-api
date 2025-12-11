from uuid import UUID

from pydantic import BaseModel

from src.user.domain.entities import Gender


class UserReadDTO(BaseModel):
    id: UUID
    apphud_id: str
    gender: Gender | None = None
    age: int | None = None
    height: int | None = None
    target: str | None = None


class UserCreateDTO(BaseModel):
    apphud_id: str
    gender: Gender | None = None
    age: int | None = None
    height: int | None = None
    target: str | None = None


class UserUpdateDTO(BaseModel):
    gender: Gender | None = None
    age: int | None = None
    height: int | None = None
    target: str | None = None


class UserAuthorizeDTO(BaseModel):
    user_id: UUID


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
