from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.announcement import (
    AnnouncementCreate,
    AnnouncementListItem,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from schemas.common import ApiResponse, PaginatedData
from controllers.announcement_controller import AnnouncementController

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post(
    "",
    response_model=ApiResponse[AnnouncementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar anúncio de venda",
)
def create_announcement(
    data: AnnouncementCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.create_announcement(current_user, data)
    return ApiResponse(data=service.to_response(announcement))


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[AnnouncementListItem]],
    summary="Listar anúncios do marketplace",
)
def list_announcements(
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(default="active", alias="status"),
    seller_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[AnnouncementListItem]]:
    service = AnnouncementController(db)
    items, total = service.list_announcements(
        status=status_filter,
        seller_id=seller_id,
        page=page,
        page_size=page_size,
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
    "/{announcement_id}",
    response_model=ApiResponse[AnnouncementResponse],
    summary="Visualizar detalhes de um anúncio",
)
def get_announcement(
    announcement_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    service.increment_views(announcement)
    return ApiResponse(data=service.to_response(announcement))


@router.put(
    "/{announcement_id}",
    response_model=ApiResponse[AnnouncementResponse],
    summary="Atualizar anúncio",
)
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    updated = service.update_announcement(announcement, current_user, data)
    return ApiResponse(data=service.to_response(updated))


@router.delete(
    "/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Apagar anúncio",
)
def delete_announcement(
    announcement_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    service.delete_announcement(announcement, current_user)


@router.post(
    "/{announcement_id}/publish",
    response_model=ApiResponse[AnnouncementResponse],
    summary="Publicar anúncio no marketplace",
)
def publish_announcement(
    announcement_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    published = service.publish_announcement(announcement, current_user)
    return ApiResponse(data=service.to_response(published))


@router.post(
    "/{announcement_id}/reserve",
    response_model=ApiResponse[AnnouncementResponse],
    summary="Reservar anúncio",
)
def reserve_announcement(
    announcement_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    reserved = service.reserve_announcement(announcement, current_user)
    return ApiResponse(data=service.to_response(reserved))


@router.post(
    "/{announcement_id}/deactivate",
    response_model=ApiResponse[AnnouncementResponse],
    summary="Desativar anúncio",
)
def deactivate_announcement(
    announcement_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AnnouncementResponse]:
    service = AnnouncementController(db)
    announcement = service.get_announcement(announcement_id)
    deactivated = service.deactivate_announcement(announcement, current_user)
    return ApiResponse(data=service.to_response(deactivated))
