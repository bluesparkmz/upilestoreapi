from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from core.exceptions import ForbiddenError, NotFoundError
from models.announcement import Announcement, AnnouncementStatus
from models.product import Product
from models.product_image import ProductImage
from models.product_like import ProductLike
from models.user import User
from schemas.product import ProductCreate, ProductImageCreate, ProductListItem, ProductResponse, ProductUpdate


from datetime import datetime, timezone

class ProductController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_product(self, owner: User, data: ProductCreate) -> Product:
        payload = data.model_dump()

        # Extrair campos relacionados com o anúncio/preço
        price = payload.pop("price", None)
        currency = payload.pop("currency", "MZN")
        quantity = payload.pop("quantity", 1)
        auto_publish = payload.pop("auto_publish", True)

        if payload.get("type") is not None:
            payload["type"] = payload["type"].value

        product = Product(owner_id=owner.id, **payload)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        # Se o preço for fornecido, criar o anúncio automaticamente!
        if price is not None:
            status_val = AnnouncementStatus.ACTIVE.value if auto_publish else AnnouncementStatus.DRAFT.value
            announcement = Announcement(
                product_id=product.id,
                seller_id=owner.id,
                price=price,
                currency=currency,
                quantity=quantity,
                status=status_val,
                published_at=datetime.now(timezone.utc) if auto_publish else None,
            )
            self.db.add(announcement)
            self.db.commit()

        return self.get_product(product.id)

    def get_product(self, product_id: int) -> Product:
        product = self.db.scalar(
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == product_id)
        )
        if product is None:
            raise NotFoundError("Obra não encontrada")
        return product

    def update_product(self, product: Product, owner: User, data: ProductUpdate) -> Product:
        if product.owner_id != owner.id:
            raise ForbiddenError("Apenas o proprietário pode editar a obra")

        update_data = data.model_dump(exclude_unset=True)

        # Extrair dados de preço/anúncio se fornecidos
        price = update_data.pop("price", None)
        currency = update_data.pop("currency", None)
        quantity = update_data.pop("quantity", None)

        if "type" in update_data and update_data["type"] is not None:
            update_data["type"] = update_data["type"].value

        for field, value in update_data.items():
            setattr(product, field, value)

        # Atualizar ou criar anúncio se preço foi especificado
        if price is not None or currency is not None or quantity is not None:
            announcement = self.db.scalar(
                select(Announcement)
                .where(
                    Announcement.product_id == product.id,
                    Announcement.status.in_([AnnouncementStatus.ACTIVE.value, AnnouncementStatus.DRAFT.value]),
                )
                .order_by(Announcement.created_at.desc())
            )
            if announcement:
                if price is not None:
                    announcement.price = price
                if currency is not None:
                    announcement.currency = currency
                if quantity is not None:
                    announcement.quantity = quantity
            else:
                announcement = Announcement(
                    product_id=product.id,
                    seller_id=owner.id,
                    price=price or 0.0,
                    currency=currency or "MZN",
                    quantity=quantity or 1,
                    status=AnnouncementStatus.ACTIVE.value,
                    published_at=datetime.now(timezone.utc),
                )
                self.db.add(announcement)

        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product: Product, owner: User) -> None:
        if product.owner_id != owner.id:
            raise ForbiddenError("Apenas o proprietário pode apagar a obra")

        self.db.delete(product)
        self.db.commit()

    def list_products(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        product_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        current_user: User | None = None,
    ) -> tuple[list[ProductListItem], int]:
        query = select(Product)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.artist.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

        if category:
            query = query.where(Product.category == category)

        if product_type:
            query = query.where(Product.type == product_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        if sort_by == "price":
            query = query.outerjoin(Announcement, Announcement.product_id == Product.id).where(
                or_(Announcement.status == AnnouncementStatus.ACTIVE.value, Announcement.id.is_(None))
            )
            order_column = Announcement.price
        else:
            order_column = Product.created_at

        if sort_order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        offset = (page - 1) * page_size
        products = self.db.scalars(query.offset(offset).limit(page_size)).all()

        items: list[ProductListItem] = []
        for product in products:
            items.append(self._build_list_item(product, current_user))

        return items, total

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

    def _get_primary_image(self, product_id: int) -> str | None:
        image = self.db.scalar(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.is_primary.desc(), ProductImage.id.asc())
        )
        return image.image_url if image else None

    def _get_views(self, product_id: int) -> int:
        return (
            self.db.scalar(
                select(func.coalesce(func.sum(Announcement.views), 0)).where(
                    Announcement.product_id == product_id
                )
            )
            or 0
        )

    def _get_active_price(self, product_id: int) -> tuple[float | None, str | None]:
        announcement = self.db.scalar(
            select(Announcement)
            .where(Announcement.product_id == product_id)
            .order_by(Announcement.created_at.desc())
        )
        if announcement:
            return float(announcement.price), announcement.currency
        return None, None

    def _build_list_item(self, product: Product, current_user: User | None) -> ProductListItem:
        price, currency = self._get_active_price(product.id)
        return ProductListItem(
            id=product.id,
            owner_id=product.owner_id,
            title=product.title,
            artist=product.artist,
            category=product.category,
            type=product.type,
            primary_image=self._get_primary_image(product.id),
            likes_count=self._get_likes_count(product.id),
            liked_by_me=self._is_liked_by_user(product.id, current_user.id if current_user else None),
            views=self._get_views(product.id),
            price=price,
            currency=currency,
            created_at=product.created_at,
        )

    def build_product_response(self, product: Product, current_user: User | None = None) -> ProductResponse:
        price, currency = self._get_active_price(product.id)
        if price is None and product.announcements:
            last_ann = product.announcements[-1]
            price = float(last_ann.price)
            currency = last_ann.currency
        return ProductResponse(
            id=product.id,
            owner_id=product.owner_id,
            title=product.title,
            description=product.description,
            category=product.category,
            type=product.type,
            artist=product.artist,
            year=product.year,
            material=product.material,
            dimensions=product.dimensions,
            condition=product.condition,
            price=price,
            currency=currency,
            created_at=product.created_at,
            updated_at=product.updated_at,
            images=product.images,
            likes_count=self._get_likes_count(product.id),
            liked_by_me=self._is_liked_by_user(product.id, current_user.id if current_user else None),
            primary_image=self._get_primary_image(product.id),
            views=self._get_views(product.id),
        )

    def add_image(self, product: Product, owner: User, data: ProductImageCreate) -> ProductImage:
        if product.owner_id != owner.id:
            raise ForbiddenError("Apenas o proprietário pode gerenciar imagens")

        if data.is_primary:
            for image in product.images:
                image.is_primary = False

        image = ProductImage(
            product_id=product.id,
            image_url=data.image_url,
            is_primary=data.is_primary,
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def delete_image(self, product: Product, image_id: int, owner: User) -> None:
        if product.owner_id != owner.id:
            raise ForbiddenError("Apenas o proprietário pode gerenciar imagens")

        image = self.db.scalar(
            select(ProductImage).where(
                ProductImage.id == image_id,
                ProductImage.product_id == product.id,
            )
        )
        if image is None:
            raise NotFoundError("Imagem não encontrada")

        self.db.delete(image)
        self.db.commit()

    def set_primary_image(self, product: Product, image_id: int, owner: User) -> ProductImage:
        if product.owner_id != owner.id:
            raise ForbiddenError("Apenas o proprietário pode gerenciar imagens")

        image = self.db.scalar(
            select(ProductImage).where(
                ProductImage.id == image_id,
                ProductImage.product_id == product.id,
            )
        )
        if image is None:
            raise NotFoundError("Imagem não encontrada")

        for img in product.images:
            img.is_primary = False

        image.is_primary = True
        self.db.commit()
        self.db.refresh(image)
        return image
