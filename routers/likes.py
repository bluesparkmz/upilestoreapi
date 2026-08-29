from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user, get_optional_current_user
from models.user import User
from schemas.common import ApiResponse
from schemas.like import LikeActionResponse, LikeResponse
from controllers.like_controller import LikeController

router = APIRouter(prefix="/products", tags=["Likes"])


@router.post(
    "/{product_id}/like",
    response_model=ApiResponse[LikeActionResponse],
    summary="Dar like em uma obra",
)
def like_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[LikeActionResponse]:
    result = LikeController(db).like_product(product_id, current_user)
    return ApiResponse(data=result)


@router.delete(
    "/{product_id}/like",
    response_model=ApiResponse[LikeActionResponse],
    summary="Remover like de uma obra",
)
def unlike_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[LikeActionResponse]:
    result = LikeController(db).unlike_product(product_id, current_user)
    return ApiResponse(data=result)


@router.get(
    "/{product_id}/likes",
    response_model=ApiResponse[LikeResponse],
    summary="Obter contagem de likes de uma obra",
)
def get_product_likes(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> ApiResponse[LikeResponse]:
    result = LikeController(db).get_likes_info(product_id, current_user)
    return ApiResponse(data=result)
