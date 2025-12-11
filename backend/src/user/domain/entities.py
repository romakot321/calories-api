from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Gender = Literal["f", "m"]


class User(BaseModel):
    id: UUID
    apphud_id: str
    gender: Gender | None = None
    age: int | None = None
    height: int | None = None
    target: str | None = None


class UserUpdate(BaseModel):
    gender: Gender | None = None
    age: int | None = None
    height: int | None = None
    target: str | None = None


class UserFilters(BaseModel):
    count: int
    offset: int
