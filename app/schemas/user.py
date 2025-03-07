from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    username: str


class UserCreateSchema(BaseModel):
    username: str

