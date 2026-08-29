from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse, PaginatedData
from schemas.order import OrderCreate, OrderResponse
from controllers.order_controller import OrderController

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=ApiResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido de compra",
)
def create_order(
    data: OrderCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[OrderResponse]:
    service = OrderController(db)
    order = service.create_order(current_user, data)
    return ApiResponse(data=service.to_response(order))


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[OrderResponse]],
    summary="Listar pedidos do usuário",
)
def list_orders(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    as_seller: bool = Query(default=False, description="Listar vendas em vez de compras"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[OrderResponse]]:
    service = OrderController(db)
    orders, total = service.list_orders(
        current_user,
        as_buyer=not as_seller,
        page=page,
        page_size=page_size,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=[service.to_response(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.get(
    "/{order_id}",
    response_model=ApiResponse[OrderResponse],
    summary="Visualizar detalhes de um pedido",
)
def get_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[OrderResponse]:
    service = OrderController(db)
    order = service.get_order(order_id)
    if order.buyer_id != current_user.id and not any(
        item.seller_id == current_user.id for item in order.items
    ):
        from core.exceptions import ForbiddenError

        raise ForbiddenError("Acesso negado ao pedido")
    return ApiResponse(data=service.to_response(order))


@router.post(
    "/{order_id}/cancel",
    response_model=ApiResponse[OrderResponse],
    summary="Cancelar pedido",
)
def cancel_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[OrderResponse]:
    service = OrderController(db)
    order = service.get_order(order_id)
    cancelled = service.cancel_order(order, current_user)
    return ApiResponse(data=service.to_response(cancelled))
