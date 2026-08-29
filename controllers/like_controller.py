from sqlalchemy import func, select
from sqlalchemy.orm import Session

from controllers.notification_controller import NotificationController
from core.exceptions import ConflictError, NotFoundError
from models.notification import NotificationType
from models.product import Product
from models.product_like import ProductLike
from models.user import User
from schemas.like import LikeActionResponse, LikeResponse


class LikeController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_likes_info(self, product_id: int, user: User | None = None) -> LikeResponse:
        self._ensure_product_exists(product_id)
        return LikeResponse(
            likes_count=self._count_likes(product_id),
            liked_by_me=self._is_liked(product_id, user.id if user else None),
        )

    def like_product(self, product_id: int, user: User) -> LikeActionResponse:
        self._ensure_product_exists(product_id)

        existing = self.db.scalar(
            select(ProductLike).where(
                ProductLike.product_id == product_id,
                ProductLike.user_id == user.id,
            )
        )
        if existing:
            return LikeActionResponse(
                message="Like já existe",
                likes_count=self._count_likes(product_id),
                liked_by_me=True,
            )

        like = ProductLike(user_id=user.id, product_id=product_id)
        self.db.add(like)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise ConflictError("Like duplicado") from exc

        # Notificar o dono da obra (se não for o próprio a dar like)
        product = self.db.get(Product, product_id)
        if product and product.owner_id != user.id:
            try:
                NotificationController(self.db).create(
                    user_id=product.owner_id,
                    type=NotificationType.LIKE,
                    title="Nova curtida na tua obra!",
                    body=f"{user.name} curtiu \"{product.title}\"",
                    entity_type="product",
                    entity_id=product_id,
                )
            except Exception:
                pass  # Notificação falhou mas o like foi registado

        return LikeActionResponse(
            message="Like adicionado",
            likes_count=self._count_likes(product_id),
            liked_by_me=True,
        )

    def unlike_product(self, product_id: int, user: User) -> LikeActionResponse:
        self._ensure_product_exists(product_id)

        like = self.db.scalar(
            select(ProductLike).where(
                ProductLike.product_id == product_id,
                ProductLike.user_id == user.id,
            )
        )
        if like is None:
            return LikeActionResponse(
                message="Like não encontrado",
                likes_count=self._count_likes(product_id),
                liked_by_me=False,
            )

        self.db.delete(like)
        self.db.commit()

        return LikeActionResponse(
            message="Like removido",
            likes_count=self._count_likes(product_id),
            liked_by_me=False,
        )

    def _ensure_product_exists(self, product_id: int) -> None:
        if self.db.get(Product, product_id) is None:
            raise NotFoundError("Obra não encontrada")

    def _count_likes(self, product_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count()).select_from(ProductLike).where(ProductLike.product_id == product_id)
            )
            or 0
        )

    def _is_liked(self, product_id: int, user_id: int | None) -> bool:
        if user_id is None:
            return False
        return (
            self.db.scalar(
                select(ProductLike.id).where(
                    ProductLike.product_id == product_id,
                    ProductLike.user_id == user_id,
                )
            )
            is not None
        )
