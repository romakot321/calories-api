from uuid import UUID
from typing import Annotated
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings

security = HTTPBearer()


class TokenData(BaseModel):
    user_id: UUID


class JWTManager:
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 12 * 60 * 60

    @classmethod
    def create_access_token(cls, user_id: UUID) -> str:
        expire = datetime.now() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "user_id": str(user_id),
            "exp": expire,
            "iat": datetime.now(),
        }
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def verify_token(cls, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            user_id: str = payload.get("user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(user_id=UUID(user_id))
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


async def get_current_user_id(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> UUID:
    token_data = JWTManager.verify_token(credentials.credentials)
    return token_data.user_id


async def get_current_user_id_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UUID | None:
    if credentials is None:
        return None
    try:
        token_data = JWTManager.verify_token(credentials.credentials)
        return token_data.user_id
    except HTTPException:
        return None
