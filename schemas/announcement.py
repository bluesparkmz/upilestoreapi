from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AnnouncementStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    INACTIVE = "inactive"


class AnnouncementCreate(BaseModel):
    product_id: int
    price: float = Field(gt=0)
    currency: str = Field(default="MZN", max_length=10)
    quantity: int = Field(default=1, ge=1)


class AnnouncementUpdate(BaseModel):
    price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, max_length=10)
    quantity: int | None = Field(default=None, ge=0)
    expires_at: datetime | None = None


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    seller_id: int
    price: float
    currency: str
    quantity: int
    status: str
    views: int
    published_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AnnouncementListItem(BaseModel):
    id: int
    product_id: int
    seller_id: int
    title: str | None = None
    artist: str | None = None
    primary_image: str | None = None
    price: float
    currency: str
    quantity: int
    status: str
    views: int
    published_at: datetime | None
    created_at: datetime
