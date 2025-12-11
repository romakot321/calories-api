from typing import Annotated

from fastapi import Depends

from src.db.dependencies import DBAsyncSessionDep
from src.user.infrastructure.uow import UserUnitOfWork
from src.user.application.interfaces.user_uow import IUserUnitOfWork


def get_user_uow(session: DBAsyncSessionDep) -> IUserUnitOfWork:
    return UserUnitOfWork(session_factory=lambda: session)


UserUoWDepend = Annotated[IUserUnitOfWork, Depends(get_user_uow)]
