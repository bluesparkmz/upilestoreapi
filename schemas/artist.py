from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArtistListItem(BaseModel):
    """Resumo de um artista para listagens."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    avatar: str | None
    bio: str | None
    location: str | None
    is_verified: bool
    products_count: int = 0
    followers_count: int = 0
    is_following: bool = False
    created_at: datetime


class ArtistDetailResponse(BaseModel):
    """Perfil detalhado do artista com estatísticas completas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    avatar: str | None
    bio: str | None
    phone: str | None
    location: str | None
    is_verified: bool
    products_count: int = 0
    total_likes: int = 0
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False
    created_at: datetime


class FollowActionResponse(BaseModel):
    """Resposta ao seguir ou deixar de seguir um artista."""

    message: str
    artist_id: int
    followers_count: int
    is_following: bool
