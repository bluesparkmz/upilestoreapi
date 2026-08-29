from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from controllers.notification_controller import NotificationController
from core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from models.announcement import Announcement, AnnouncementStatus
from models.notification import NotificationType
from models.product import Product
from models.product_image import ProductImage
from models.user import User
from schemas.announcement import AnnouncementCreate, AnnouncementListItem, AnnouncementResponse, AnnouncementUpdate


class AnnouncementController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_announcement(self, seller: User, data: AnnouncementCreate) -> Announcement:
        product = self.db.get(Product, data.product_id)
        if product is None:
            raise NotFoundError("Obra não encontrada")

        if product.owner_id != seller.id:
            raise ForbiddenError("Somente o proprietário da obra pode criar um anúncio")

        announcement = Announcement(
            product_id=product.id,
            seller_id=seller.id,
            price=data.price,
            currency=data.currency,
            quantity=data.quantity,
            status=AnnouncementStatus.DRAFT.value,
        )
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def get_announcement(self, announcement_id: int) -> Announcement:
        announcement = self.db.get(Announcement, announcement_id)
        if announcement is None:
            raise NotFoundError("Anúncio não encontrado")
        return announcement

    def update_announcement(
        self, announcement: Announcement, seller: User, data: AnnouncementUpdate
    ) -> Announcement:
        if announcement.seller_id != seller.id:
            raise ForbiddenError("Somente o proprietário pode editar o anúncio")

        if announcement.status == AnnouncementStatus.SOLD.value:
            raise BadRequestError("Anúncio vendido não pode ser editado")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(announcement, field, value)

        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def delete_announcement(self, announcement: Announcement, seller: User) -> None:
        if announcement.seller_id != seller.id:
            raise ForbiddenError("Somente o proprietário pode apagar o anúncio")

        self.db.delete(announcement)
        self.db.commit()

    def publish_announcement(self, announcement: Announcement, seller: User) -> Announcement:
        if announcement.seller_id != seller.id:
            raise ForbiddenError("Somente o proprietário pode publicar o anúncio")

        if announcement.quantity <= 0:
            raise BadRequestError("Quantidade deve ser maior que zero para publicar")

        announcement.status = AnnouncementStatus.ACTIVE.value
        announcement.published_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def reserve_announcement(self, announcement: Announcement, seller: User) -> Announcement:
        if announcement.seller_id != seller.id:
            raise ForbiddenError("Somente o proprietário pode reservar o anúncio")

        if announcement.status != AnnouncementStatus.ACTIVE.value:
            raise BadRequestError("Somente anúncios ativos podem ser reservados")

        announcement.status = AnnouncementStatus.RESERVED.value
        self.db.commit()
        self.db.refresh(announcement)

        # Notificar o vendedor sobre a reserva
        try:
            product = self.db.get(Product, announcement.product_id)
            NotificationController(self.db).create(
                user_id=announcement.seller_id,
                type=NotificationType.RESERVATION,
                title="O teu anúncio foi reservado!",
                body=f'"{product.title if product else "Produto"}" foi marcado como reservado.',
                entity_type="announcement",
                entity_id=announcement.id,
            )
        except Exception:
            pass  # Não bloquear a operação por falha na notificação

        return announcement

    def deactivate_announcement(self, announcement: Announcement, seller: User) -> Announcement:
        if announcement.seller_id != seller.id:
            raise ForbiddenError("Somente o proprietário pode desativar o anúncio")

        announcement.status = AnnouncementStatus.INACTIVE.value
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def list_announcements(
        self,
        *,
        status: str | None = AnnouncementStatus.ACTIVE.value,
        seller_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AnnouncementListItem], int]:
        query = select(Announcement)

        if status:
            query = query.where(Announcement.status == status)

        if seller_id:
            query = query.where(Announcement.seller_id == seller_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        query = query.order_by(Announcement.created_at.desc())
        offset = (page - 1) * page_size
        announcements = self.db.scalars(query.offset(offset).limit(page_size)).all()

        items = [self._build_list_item(a) for a in announcements]
        return items, total

    def increment_views(self, announcement: Announcement) -> None:
        announcement.views += 1
        self.db.commit()

    def _get_primary_image(self, product_id: int) -> str | None:
        image = self.db.scalar(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.is_primary.desc(), ProductImage.id.asc())
        )
        return image.image_url if image else None

    def _build_list_item(self, announcement: Announcement) -> AnnouncementListItem:
        product = self.db.get(Product, announcement.product_id)
        return AnnouncementListItem(
            id=announcement.id,
            product_id=announcement.product_id,
            seller_id=announcement.seller_id,
            title=product.title if product else None,
            artist=product.artist if product else None,
            primary_image=self._get_primary_image(announcement.product_id),
            price=float(announcement.price),
            currency=announcement.currency,
            quantity=announcement.quantity,
            status=announcement.status,
            views=announcement.views,
            published_at=announcement.published_at,
            created_at=announcement.created_at,
        )

    def to_response(self, announcement: Announcement) -> AnnouncementResponse:
        return AnnouncementResponse(
            id=announcement.id,
            product_id=announcement.product_id,
            seller_id=announcement.seller_id,
            price=float(announcement.price),
            currency=announcement.currency,
            quantity=announcement.quantity,
            status=announcement.status,
            views=announcement.views,
            published_at=announcement.published_at,
            expires_at=announcement.expires_at,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at,
        )
