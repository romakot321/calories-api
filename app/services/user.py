from fastapi import Depends

from app.repositories.logmeal import LogmealRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserSchema, UserCreateSchema
from app.db.tables import User


class UserService:
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        logmeal_repository: LogmealRepository = Depends(),
    ):
        self.logmeal_repository = logmeal_repository
        self.user_repository = user_repository

    async def create(self, schema: UserCreateSchema) -> UserSchema:
        token = await self.logmeal_repository.create_user(schema.username)
        model = User(username=schema.username, token=token)
        model = await self.user_repository.create(model)
        return UserSchema.model_validate(model)
