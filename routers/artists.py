from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from controllers.artist_controller import ArtistController
from core.database import get_db
from dependencies.auth import get_current_active_user, get_optional_current_user
from models.user import User
from schemas.artist import ArtistDetailResponse, ArtistListItem, FollowActionResponse
from schemas.common import ApiResponse, PaginatedData
from schemas.product import ProductListItem

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[ArtistListItem]],
    summary="Listar artistas",
    description="Retorna a lista paginada de artistas com filtros por pesquisa, localização, verificação e ordenação.",
)
def list_artists(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    search: str | None = Query(default=None, description="Pesquisar por nome, username ou bio"),
    location: str | None = Query(default=None, description="Filtrar por cidade/localização"),
    is_verified: bool | None = Query(default=None, description="Filtrar artistas verificados"),
    sort_by: str = Query(default="popular", pattern="^(popular|recent|name)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[ArtistListItem]]:
    controller = ArtistController(db)
    items, total = controller.list_artists(
        search=search,
        location=location,
        is_verified=is_verified,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.get(
    "/{artist_id}",
    response_model=ApiResponse[ArtistDetailResponse],
    summary="Obter perfil e estatísticas de um artista",
)
def get_artist_detail(
    artist_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> ApiResponse[ArtistDetailResponse]:
    detail = ArtistController(db).get_artist_detail(artist_id, current_user)
    return ApiResponse(data=detail)


@router.get(
    "/{artist_id}/products",
    response_model=ApiResponse[PaginatedData[ProductListItem]],
    summary="Listar obras de um artista específico",
)
def get_artist_products(
    artist_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[ProductListItem]]:
    controller = ArtistController(db)
    items, total = controller.get_artist_products(
        artist_id,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.post(
    "/{artist_id}/follow",
    response_model=ApiResponse[FollowActionResponse],
    summary="Seguir um artista",
)
def follow_artist(
    artist_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[FollowActionResponse]:
    res = ArtistController(db).follow_artist(current_user, artist_id)
    return ApiResponse(data=res)


@router.delete(
    "/{artist_id}/follow",
    response_model=ApiResponse[FollowActionResponse],
    summary="Deixar de seguir um artista",
)
def unfollow_artist(
    artist_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[FollowActionResponse]:
    res = ArtistController(db).unfollow_artist(current_user, artist_id)
    return ApiResponse(data=res)
