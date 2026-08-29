from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


# Modos de ordenação disponíveis no feed
FeedSort = Literal["recent", "oldest", "trending", "price_asc", "price_desc", "for_you"]


class FeedSellerInfo(BaseModel):
    """Informação resumida do vendedor num item do feed."""

    id: int
    name: str
    username: str
    avatar: str | None
    location: str | None
    is_verified: bool


class FeedItem(BaseModel):
    """Item unificado do feed — combina produto + anúncio (se houver) + vendedor."""

    model_config = ConfigDict(from_attributes=True)

    announcement_id: int | None = None
    product_id: int
    title: str
    description: str | None = None
    artist: str | None = None
    category: str | None = None
    type: str | None = None
    primary_image: str | None = None
    price: float | None = None
    currency: str | None = None
    views: int = 0
    likes_count: int = 0
    liked_by_me: bool = False
    seller: FeedSellerInfo
    published_at: datetime | None = None
    created_at: datetime
