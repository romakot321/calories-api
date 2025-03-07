from fastapi import APIRouter, Depends

from app.schemas.user import UserCreateSchema, UserSchema
from app.services.user import UserService

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post("", response_model=UserSchema)
async def create_user(schema: UserCreateSchema, service: UserService = Depends()):
    return await service.create(schema)
