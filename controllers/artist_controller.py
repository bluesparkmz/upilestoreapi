from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from controllers.product_controller import ProductController
from core.exceptions import BadRequestError, ConflictError, NotFoundError
from models.product import Product
from models.product_like import ProductLike
from models.user import User
from models.user_follow import UserFollow
from schemas.artist import ArtistDetailResponse, ArtistListItem, FollowActionResponse
from schemas.product import ProductListItem


class ArtistController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_artists(
        self,
        *,
        search: str | None = None,
        location: str | None = None,
        is_verified: bool | None = None,
        sort_by: str = "popular",  # "popular", "recent", "name"
        page: int = 1,
        page_size: int = 20,
        current_user: User | None = None,
    ) -> tuple[list[ArtistListItem], int]:
        # Consideramos artistas utilizadores ativos que têm produtos ou são verificados
        query = select(User).where(User.is_active == True)  # noqa: E712

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.name.ilike(pattern),
                    User.username.ilike(pattern),
                    User.bio.ilike(pattern),
                )
            )

        if location:
            query = query.where(User.location.ilike(f"%{location}%"))

        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Sub-query para contagem de obras por artista
        products_sq = (
            select(Product.owner_id, func.count(Product.id).label("p_count"))
            .group_by(Product.owner_id)
            .subquery()
        )

        query = query.outerjoin(products_sq, products_sq.c.owner_id == User.id)

        if sort_by == "popular":
            # Ordenar por total de obras desc
            query = query.order_by(func.coalesce(products_sq.c.p_count, 0).desc(), User.name.asc())
        elif sort_by == "recent":
            query = query.order_by(User.created_at.desc())
        elif sort_by == "name":
            query = query.order_by(User.name.asc())

        offset = (page - 1) * page_size
        users = list(self.db.scalars(query.offset(offset).limit(page_size)).all())

        items = [self._build_artist_item(user, current_user) for user in users]
        return items, total

    def get_artist_detail(self, artist_id: int, current_user: User | None = None) -> ArtistDetailResponse:
        artist = self.db.get(User, artist_id)
        if artist is None or not artist.is_active:
            raise NotFoundError("Artista não encontrado")

        products_count = self._get_products_count(artist.id)
        total_likes = self._get_total_likes(artist.id)
        followers_count = self._get_followers_count(artist.id)
        following_count = self._get_following_count(artist.id)
        is_following = self._is_following(current_user.id if current_user else None, artist.id)

        return ArtistDetailResponse(
            id=artist.id,
            name=artist.name,
            username=artist.username,
            avatar=artist.avatar,
            bio=artist.bio,
            phone=artist.phone,
            location=artist.location,
            is_verified=artist.is_verified,
            products_count=products_count,
            total_likes=total_likes,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
            created_at=artist.created_at,
        )

    def get_artist_products(
        self,
        artist_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        current_user: User | None = None,
    ) -> tuple[list[ProductListItem], int]:
        artist = self.db.get(User, artist_id)
        if artist is None or not artist.is_active:
            raise NotFoundError("Artista não encontrado")

        product_ctrl = ProductController(self.db)
        return product_ctrl.list_products(
            page=page,
            page_size=page_size,
            current_user=current_user,
        )

    def follow_artist(self, follower: User, artist_id: int) -> FollowActionResponse:
        if follower.id == artist_id:
            raise BadRequestError("Não podes seguir a ti próprio")

        artist = self.db.get(User, artist_id)
        if artist is None or not artist.is_active:
            raise NotFoundError("Artista não encontrado")

        existing = self.db.scalar(
            select(UserFollow).where(
                UserFollow.follower_id == follower.id,
                UserFollow.artist_id == artist_id,
            )
        )
        if existing:
            return FollowActionResponse(
                message="Já segues este artista",
                artist_id=artist_id,
                followers_count=self._get_followers_count(artist_id),
                is_following=True,
            )

        follow = UserFollow(follower_id=follower.id, artist_id=artist_id)
        self.db.add(follow)
        self.db.commit()

        return FollowActionResponse(
            message="Artista seguido com sucesso",
            artist_id=artist_id,
            followers_count=self._get_followers_count(artist_id),
            is_following=True,
        )

    def unfollow_artist(self, follower: User, artist_id: int) -> FollowActionResponse:
        artist = self.db.get(User, artist_id)
        if artist is None or not artist.is_active:
            raise NotFoundError("Artista não encontrado")

        follow = self.db.scalar(
            select(UserFollow).where(
                UserFollow.follower_id == follower.id,
                UserFollow.artist_id == artist_id,
            )
        )
        if follow:
            self.db.delete(follow)
            self.db.commit()

        return FollowActionResponse(
            message="Deixaste de seguir este artista",
            artist_id=artist_id,
            followers_count=self._get_followers_count(artist_id),
            is_following=False,
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _get_products_count(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Product).where(Product.owner_id == user_id)
        ) or 0

    def _get_total_likes(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(ProductLike)
            .join(Product, Product.id == ProductLike.product_id)
            .where(Product.owner_id == user_id)
        ) or 0

    def _get_followers_count(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(UserFollow).where(UserFollow.artist_id == user_id)
        ) or 0

    def _get_following_count(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == user_id)
        ) or 0

    def _is_following(self, follower_id: int | None, artist_id: int) -> bool:
        if follower_id is None:
            return False
        return (
            self.db.scalar(
                select(UserFollow.id).where(
                    UserFollow.follower_id == follower_id,
                    UserFollow.artist_id == artist_id,
                )
            )
            is not None
        )

    def _build_artist_item(self, user: User, current_user: User | None) -> ArtistListItem:
        return ArtistListItem(
            id=user.id,
            name=user.name,
            username=user.username,
            avatar=user.avatar,
            bio=user.bio,
            location=user.location,
            is_verified=user.is_verified,
            products_count=self._get_products_count(user.id),
            followers_count=self._get_followers_count(user.id),
            is_following=self._is_following(current_user.id if current_user else None, user.id),
            created_at=user.created_at,
        )
