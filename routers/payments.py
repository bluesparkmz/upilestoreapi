from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse
from schemas.payment import PaymentCreate, PaymentResponse
from controllers.payment_controller import PaymentController

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "",
    response_model=ApiResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar pagamento de um pedido",
)
def create_payment(
    data: PaymentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    service = PaymentController(db)
    payment = service.create_payment(current_user, data)
    return ApiResponse(data=service.to_response(payment))


@router.get(
    "/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    summary="Consultar pagamento",
)
def get_payment(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    service = PaymentController(db)
    payment = service.get_payment(payment_id)
    order = payment.order
    if order.buyer_id != current_user.id:
        from core.exceptions import ForbiddenError

        raise ForbiddenError("Acesso negado")
    return ApiResponse(data=service.to_response(payment))
