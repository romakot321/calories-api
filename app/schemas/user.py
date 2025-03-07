from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(BaseModel):
    username: str

