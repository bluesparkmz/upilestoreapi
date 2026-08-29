from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from controllers.notification_controller import NotificationController
from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse, MessageData, PaginatedData
from schemas.notification import NotificationCount, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[NotificationResponse]],
    summary="Listar as minhas notificações",
)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    unread: bool = Query(default=False, description="Se true, retorna apenas as não lidas"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[NotificationResponse]]:
    ctrl = NotificationController(db)
    items, total = ctrl.list_notifications(
        current_user,
        unread_only=unread,
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
    "/count",
    response_model=ApiResponse[NotificationCount],
    summary="Contagem de notificações não lidas",
)
def get_notification_count(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[NotificationCount]:
    count = NotificationController(db).get_count(current_user)
    return ApiResponse(data=count)


@router.patch(
    "/read-all",
    response_model=ApiResponse[MessageData],
    summary="Marcar todas as notificações como lidas",
)
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[MessageData]:
    updated = NotificationController(db).mark_all_read(current_user)
    return ApiResponse(data=MessageData(message=f"{updated} notificação(ões) marcada(s) como lida(s)"))


@router.patch(
    "/{notification_id}/read",
    response_model=ApiResponse[NotificationResponse],
    summary="Marcar uma notificação como lida",
)
def mark_read(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[NotificationResponse]:
    notification = NotificationController(db).mark_read(current_user, notification_id)
    return ApiResponse(data=notification)
