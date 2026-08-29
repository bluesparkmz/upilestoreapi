from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from core.exceptions import BadRequestError, ConflictError, NotFoundError
from models.product import Product
from models.user import User
from schemas.admin import AdminProductUpdate, AdminUserUpdate


class AdminController:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ─── Utilizadores ─────────────────────────────────────────────────────────

    def list_users(
        self,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        is_admin: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        query = select(User)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.name.ilike(pattern),
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        users = list(self.db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(page_size)).all())

        return users, total

    def get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("Utilizador não encontrado")
        return user

    def update_user(self, user_id: int, data: AdminUserUpdate) -> User:
        user = self.get_user(user_id)

        update_data = data.model_dump(exclude_unset=True)

        # Verificar unicidade de username
        if "username" in update_data and update_data["username"] != user.username:
            existing = self.db.scalar(
                select(User).where(User.username == update_data["username"])
            )
            if existing:
                raise ConflictError("Username já está em uso")

        # Verificar unicidade de email
        if "email" in update_data and update_data["email"] != user.email:
            existing = self.db.scalar(
                select(User).where(User.email == update_data["email"])
            )
            if existing:
                raise ConflictError("Email já está em uso")

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int, current_admin: User) -> None:
        if user_id == current_admin.id:
            raise BadRequestError("Não é possível eliminar a própria conta admin")

        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()

    def toggle_active(self, user_id: int, current_admin: User) -> User:
        if user_id == current_admin.id:
            raise BadRequestError("Não é possível desativar a própria conta admin")

        user = self.get_user(user_id)
        user.is_active = not user.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def toggle_verified(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.is_verified = not user.is_verified
        self.db.commit()
        self.db.refresh(user)
        return user

    # ─── Produtos ─────────────────────────────────────────────────────────────

    def list_all_products(
        self,
        *,
        search: str | None = None,
        owner_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        query = select(Product).options(selectinload(Product.images))

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.artist.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

        if owner_id is not None:
            query = query.where(Product.owner_id == owner_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        products = list(
            self.db.scalars(query.order_by(Product.created_at.desc()).offset(offset).limit(page_size)).all()
        )

        return products, total

    def get_product(self, product_id: int) -> Product:
        product = self.db.scalar(
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == product_id)
        )
        if product is None:
            raise NotFoundError("Produto não encontrado")
        return product

    def admin_update_product(self, product_id: int, data: AdminProductUpdate) -> Product:
        product = self.get_product(product_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def admin_delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        self.db.delete(product)
        self.db.commit()
