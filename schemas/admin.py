from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Utilizadores ────────────────────────────────────────────────────────────

class AdminUserResponse(BaseModel):
    """Resposta completa de um utilizador para o painel admin."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    email: EmailStr
    avatar: str | None
    bio: str | None
    phone: str | None
    location: str | None
    is_verified: bool
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class AdminUserUpdate(BaseModel):
    """Payload para o admin editar um utilizador."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    username: str | None = Field(
        default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=255)
    bio: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    is_admin: bool | None = None


# ─── Produtos ─────────────────────────────────────────────────────────────────

class AdminProductUpdate(BaseModel):
    """Payload para o admin editar qualquer produto (sem restrição de owner)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    type: str | None = Field(default=None, max_length=50)
    artist: str | None = Field(default=None, max_length=255)
    year: int | None = Field(default=None, ge=1, le=9999)
    material: str | None = Field(default=None, max_length=255)
    dimensions: str | None = Field(default=None, max_length=255)
    condition: str | None = Field(default=None, max_length=100)
