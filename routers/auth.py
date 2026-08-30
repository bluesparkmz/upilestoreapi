from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse
from schemas.user import TokenData, TokenRefresh, UserLogin, UserRegister, UserResponse
from controllers.auth_controller import AuthController

router = APIRouter(prefix="/auth", tags=["Authentication"])


import os
from core.config import get_settings


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registar novo usuário",
)
def register(
    data: UserRegister,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[UserResponse]:
    user = AuthController(db).register(data)
    admin_env = (os.getenv("ADMIN") or os.getenv("ADMIN_EMAIL") or "").strip().lower()
    if admin_env and (user.email.lower() == admin_env or user.username.lower() == admin_env):
        user.is_admin = True
        user.is_verified = True
        user.is_active = True
        db.commit()
        db.refresh(user)
    return ApiResponse(data=UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=ApiResponse[TokenData],
    summary="Login e obtenção de tokens JWT",
)
def login(
    data: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[TokenData]:
    admin_env = (os.getenv("ADMIN") or os.getenv("ADMIN_EMAIL") or "").strip().lower()
    if admin_env:
        db_user = db.query(User).filter(
            (User.email.ilike(admin_env)) | (User.username.ilike(admin_env))
        ).first()
        if db_user and not db_user.is_admin:
            db_user.is_admin = True
            db_user.is_verified = True
            db_user.is_active = True
            db.commit()

    tokens = AuthController(db).login(data)
    return ApiResponse(data=tokens)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenData],
    summary="Renovar tokens de acesso",
)
def refresh_token(
    data: TokenRefresh,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[TokenData]:
    tokens = AuthController(db).refresh_tokens(data.refresh_token)
    return ApiResponse(data=tokens)


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Obter perfil do usuário autenticado",
)
def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[UserResponse]:
    return ApiResponse(data=UserResponse.model_validate(current_user))
