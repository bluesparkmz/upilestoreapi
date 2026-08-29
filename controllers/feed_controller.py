from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from models.announcement import Announcement, AnnouncementStatus
from models.product import Product
from models.product_image import ProductImage
from models.product_like import ProductLike
from models.user import User
from models.user_preference import UserPreference
from schemas.feed import FeedItem, FeedSellerInfo, FeedSort


class FeedController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_feed(
        self,
        *,
        sort: FeedSort = "recent",
        location: str | None = None,
        category: str | None = None,
        product_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        current_user: User | None = None,
    ) -> tuple[list[FeedItem], int]:
        # Base — consulta a partir de produtos, fazendo outerjoin com anúncio activo e dono
        query = (
            select(Product)
            .join(User, User.id == Product.owner_id)
            .outerjoin(
                Announcement,
                (Announcement.product_id == Product.id)
                & (Announcement.status == AnnouncementStatus.ACTIVE.value),
            )
            .options(
                selectinload(Product.images),
                selectinload(Product.announcements),
                selectinload(Product.owner),
            )
        )

        # ── Filtro de pesquisa ────────────────────────────────────────────────
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.artist.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

        # ── Filtro por categoria ──────────────────────────────────────────────
        if category:
            query = query.where(Product.category == category)

        # ── Filtro por tipo ───────────────────────────────────────────────────
        if product_type:
            query = query.where(Product.type == product_type)

        # ── Filtro por localização ────────────────────────────────────────────
        if location:
            query = query.where(User.location.ilike(f"%{location}%"))

        # ── Modo "for_you" — filtrar pelas preferências do utilizador ─────────
        if sort == "for_you" and current_user is not None:
            pref = self.db.scalar(
                select(UserPreference).where(UserPreference.user_id == current_user.id)
            )
            if pref and (pref.categories or pref.types):
                conditions = []
                if pref.categories:
                    conditions.append(Product.category.in_(pref.categories))
                if pref.types:
                    conditions.append(Product.type.in_(pref.types))
                query = query.where(or_(*conditions))

                if not location and pref.preferred_location:
                    query = query.where(User.location.ilike(f"%{pref.preferred_location}%"))
            else:
                sort = "trending"

        # ── Contagem total ────────────────────────────────────────────────────
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # ── Ordenação ─────────────────────────────────────────────────────────
        if sort == "recent" or sort == "for_you":
            query = query.order_by(func.coalesce(Announcement.published_at, Product.created_at).desc())
        elif sort == "oldest":
            query = query.order_by(func.coalesce(Announcement.published_at, Product.created_at).asc())
        elif sort == "price_asc":
            query = query.order_by(Announcement.price.asc().nulls_last())
        elif sort == "price_desc":
            query = query.order_by(Announcement.price.desc().nulls_last())
        elif sort == "trending":
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)

            likes_sq = (
                select(
                    ProductLike.product_id,
                    func.count(ProductLike.id).label("likes_count"),
                )
                .where(ProductLike.created_at >= week_ago)
                .group_by(ProductLike.product_id)
                .subquery()
            )

            query = (
                query.outerjoin(likes_sq, likes_sq.c.product_id == Product.id)
                .order_by(
                    (func.coalesce(Announcement.views, 0) + func.coalesce(likes_sq.c.likes_count, 0)).desc()
                )
            )

        # ── Paginação ─────────────────────────────────────────────────────────
        offset = (page - 1) * page_size
        products = list(self.db.scalars(query.offset(offset).limit(page_size)).all())

        items = [self._build_feed_item(p, current_user) for p in products]
        return items, total

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _get_primary_image(self, product_id: int) -> str | None:
        image = self.db.scalar(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.is_primary.desc(), ProductImage.id.asc())
        )
        return image.image_url if image else None

    def _get_likes_count(self, product_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(ProductLike).where(ProductLike.product_id == product_id)
        ) or 0

    def _is_liked_by_user(self, product_id: int, user_id: int | None) -> bool:
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

    def _build_feed_item(self, product: Product, current_user: User | None) -> FeedItem:
        seller = product.owner
        announcement = None
        if product.announcements:
            active_ann = [a for a in product.announcements if a.status == AnnouncementStatus.ACTIVE.value]
            announcement = active_ann[0] if active_ann else product.announcements[0]

        return FeedItem(
            announcement_id=announcement.id if announcement else None,
            product_id=product.id,
            title=product.title,
            description=product.description,
            artist=product.artist,
            category=product.category,
            type=product.type,
            primary_image=self._get_primary_image(product.id),
            price=float(announcement.price) if announcement else None,
            currency=announcement.currency if announcement else None,
            views=announcement.views if announcement else 0,
            likes_count=self._get_likes_count(product.id),
            liked_by_me=self._is_liked_by_user(product.id, current_user.id if current_user else None),
            seller=FeedSellerInfo(
                id=seller.id,
                name=seller.name,
                username=seller.username,
                avatar=seller.avatar,
                location=seller.location,
                is_verified=seller.is_verified,
            ),
            published_at=announcement.published_at if announcement else product.created_at,
            created_at=product.created_at,
        )
