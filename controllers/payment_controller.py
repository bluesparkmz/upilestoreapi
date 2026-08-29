from sqlalchemy.orm import Session

from core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from models.order import Order, OrderStatus
from models.payment import Payment, PaymentStatus
from models.user import User
from schemas.payment import PaymentCreate, PaymentResponse


class PaymentController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_payment(self, user: User, data: PaymentCreate) -> Payment:
        order = self.db.get(Order, data.order_id)
        if order is None:
            raise NotFoundError("Pedido não encontrado")

        if order.buyer_id != user.id:
            raise ForbiddenError("Somente o comprador pode iniciar pagamento")

        if order.status == OrderStatus.CANCELLED.value:
            raise BadRequestError("Pedido cancelado não pode ser pago")

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            currency=order.currency,
            method=data.method.value,
            provider=data.provider,
            status=PaymentStatus.PENDING.value,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payment(self, payment_id: int) -> Payment:
        payment = self.db.get(Payment, payment_id)
        if payment is None:
            raise NotFoundError("Pagamento não encontrado")
        return payment

    def list_payments_for_order(self, order_id: int, user: User) -> list[Payment]:
        order = self.db.get(Order, order_id)
        if order is None:
            raise NotFoundError("Pedido não encontrado")

        if order.buyer_id != user.id:
            raise ForbiddenError("Acesso negado")

        return list(order.payments)

    def to_response(self, payment: Payment) -> PaymentResponse:
        return PaymentResponse.model_validate(payment)
