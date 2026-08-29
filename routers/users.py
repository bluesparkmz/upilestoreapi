from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse
from schemas.user import UserPublicResponse, UserResponse, UserUpdate
from schemas.preference import PreferenceResponse, PreferenceUpdate
from controllers.auth_controller import AuthController
from controllers.preference_controller import PreferenceController

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Obter perfil do usuário autenticado",
)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[UserResponse]:
    return ApiResponse(data=UserResponse.model_validate(current_user))


@router.put(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Atualizar perfil do usuário autenticado",
)
def update_my_profile(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[UserResponse]:
    user = AuthController(db).update_user(current_user, data)
    return ApiResponse(data=UserResponse.model_validate(user))


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserPublicResponse],
    summary="Obter perfil público de um usuário",
)
def get_user_profile(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[UserPublicResponse]:
    user = AuthController(db).get_user_by_id(user_id)
    return ApiResponse(data=UserPublicResponse.model_validate(user))


@router.get(
    "/me/preferences",
    response_model=ApiResponse[PreferenceResponse],
    summary="Obter as minhas preferências de feed",
)
def get_my_preferences(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[PreferenceResponse]:
    pref = PreferenceController(db).get_or_create(current_user)
    return ApiResponse(data=PreferenceController(db).to_response(pref))


@router.put(
    "/me/preferences",
    response_model=ApiResponse[PreferenceResponse],
    summary="Actualizar as minhas preferências de feed",
)
def update_my_preferences(
    data: PreferenceUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[PreferenceResponse]:
    pref = PreferenceController(db).update(current_user, data)
    return ApiResponse(data=pref)
