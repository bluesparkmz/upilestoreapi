from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from controllers.notification_controller import NotificationController
from core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from models.announcement import Announcement, AnnouncementStatus
from models.notification import NotificationType
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.user import User
from schemas.order import OrderCreate, OrderResponse


class OrderController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_order(self, buyer: User, data: OrderCreate) -> Order:
        if not data.items:
            raise BadRequestError("O pedido deve conter pelo menos um item")

        try:
            order_items_data: list[dict] = []
            total_amount = Decimal("0")
            currency: str | None = None

            for item_data in data.items:
                announcement = self.db.scalar(
                    select(Announcement)
                    .where(Announcement.id == item_data.announcement_id)
                    .with_for_update()
                )
                if announcement is None:
                    raise NotFoundError(f"Anúncio {item_data.announcement_id} não encontrado")

                if announcement.status != AnnouncementStatus.ACTIVE.value:
                    raise BadRequestError(f"Anúncio {announcement.id} não está disponível para compra")

                if announcement.seller_id == buyer.id:
                    raise BadRequestError("Não é possível comprar o próprio anúncio")

                if announcement.quantity < item_data.quantity:
                    raise BadRequestError(f"Quantidade insuficiente para anúncio {announcement.id}")

                unit_price = Decimal(str(announcement.price))
                item_total = unit_price * item_data.quantity
                total_amount += item_total

                if currency is None:
                    currency = announcement.currency
                elif currency != announcement.currency:
                    raise BadRequestError("Todos os itens devem usar a mesma moeda")

                order_items_data.append(
                    {
                        "announcement": announcement,
                        "quantity": item_data.quantity,
                        "unit_price": unit_price,
                        "total_price": item_total,
                    }
                )

            order = Order(
                buyer_id=buyer.id,
                total_amount=float(total_amount),
                currency=currency or "MZN",
                status=OrderStatus.PENDING.value,
            )
            self.db.add(order)
            self.db.flush()

            for item in order_items_data:
                announcement = item["announcement"]
                order_item = OrderItem(
                    order_id=order.id,
                    announcement_id=announcement.id,
                    product_id=announcement.product_id,
                    seller_id=announcement.seller_id,
                    quantity=item["quantity"],
                    unit_price=float(item["unit_price"]),
                    total_price=float(item["total_price"]),
                )
                self.db.add(order_item)

                announcement.quantity -= item["quantity"]
                if announcement.quantity <= 0:
                    announcement.quantity = 0
                    announcement.status = AnnouncementStatus.SOLD.value

                    # Notificar o vendedor sobre a venda
                    try:
                        product_title = item["announcement"].product.title if hasattr(item["announcement"], "product") else "Produto"
                        NotificationController(self.db).create(
                            user_id=announcement.seller_id,
                            type=NotificationType.SALE,
                            title="Venda concluída! 🎉",
                            body=f'O teu anúncio foi vendido! Valor: {float(item["total_price"])} {announcement.currency}.',
                            entity_type="order",
                            entity_id=order.id,
                        )
                    except Exception:
                        pass  # Não bloquear a venda por falha na notificação

            self.db.commit()
            self.db.refresh(order)
            return self.get_order(order.id)

        except (NotFoundError, BadRequestError):
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

    def get_order(self, order_id: int) -> Order:
        order = self.db.scalar(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        if order is None:
            raise NotFoundError("Pedido não encontrado")
        return order

    def list_orders(
        self,
        user: User,
        *,
        as_buyer: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        query = select(Order).options(selectinload(Order.items))

        if as_buyer:
            query = query.where(Order.buyer_id == user.id)
        else:
            query = query.join(OrderItem).where(OrderItem.seller_id == user.id).distinct()

        total = len(self.db.scalars(query).all())
        offset = (page - 1) * page_size
        orders = self.db.scalars(query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)).all()
        return list(orders), total

    def cancel_order(self, order: Order, user: User) -> Order:
        if order.buyer_id != user.id:
            raise ForbiddenError("Somente o comprador pode cancelar o pedido")

        if order.status in (OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value):
            raise BadRequestError("Pedido não pode ser cancelado")

        try:
            for item in order.items:
                announcement = self.db.scalar(
                    select(Announcement)
                    .where(Announcement.id == item.announcement_id)
                    .with_for_update()
                )
                if announcement:
                    announcement.quantity += item.quantity
                    if announcement.status == AnnouncementStatus.SOLD.value and announcement.quantity > 0:
                        announcement.status = AnnouncementStatus.ACTIVE.value

            order.status = OrderStatus.CANCELLED.value
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise

    def to_response(self, order: Order) -> OrderResponse:
        return OrderResponse.model_validate(order)
