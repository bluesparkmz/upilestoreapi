from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductType(str, Enum):
    PINTURA = "pintura"
    ESCULTURA = "escultura"
    FOTOGRAFIA = "fotografia"
    DESENHO = "desenho"
    ARTE_DIGITAL = "arte digital"
    ARTESANATO = "artesanato"
    OUTRO = "outro"


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    type: ProductType | None = None
    artist: str | None = Field(default=None, max_length=255)
    year: int | None = None
    material: str | None = Field(default=None, max_length=255)
    dimensions: str | None = Field(default=None, max_length=255)
    condition: str | None = Field(default=None, max_length=100)
    # Preço e publicação opcional no momento da criação da obra
    price: float | None = Field(default=None, description="Preço de venda da obra")
    currency: str = Field(default="MZN", max_length=10)
    quantity: int = Field(default=1)
    auto_publish: bool = Field(default=True, description="Publicar anúncio de venda imediatamente")

    @field_validator("year", mode="before")
    @classmethod
    def clean_year(cls, v: object) -> int | None:
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            val = int(v)
            return val if 1 <= val <= 9999 else None
        except (ValueError, TypeError):
            return None

    @field_validator("price", mode="before")
    @classmethod
    def clean_price(cls, v: object) -> float | None:
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            val = float(v)
            return val if val >= 0 else 0.0
        except (ValueError, TypeError):
            return None

    @field_validator("quantity", mode="before")
    @classmethod
    def clean_quantity(cls, v: object) -> int:
        if v is None or v == "" or v == "null" or v == "undefined":
            return 1
        try:
            val = int(v)
            return val if val >= 1 else 1
        except (ValueError, TypeError):
            return 1


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    type: ProductType | None = None
    artist: str | None = Field(default=None, max_length=255)
    year: int | None = None
    material: str | None = Field(default=None, max_length=255)
    dimensions: str | None = Field(default=None, max_length=255)
    condition: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None)
    currency: str | None = Field(default=None, max_length=10)
    quantity: int | None = None

    @field_validator("year", mode="before")
    @classmethod
    def clean_update_year(cls, v: object) -> int | None:
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            val = int(v)
            return val if 1 <= val <= 9999 else None
        except (ValueError, TypeError):
            return None

    @field_validator("price", mode="before")
    @classmethod
    def clean_update_price(cls, v: object) -> float | None:
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            val = float(v)
            return val if val >= 0 else 0.0
        except (ValueError, TypeError):
            return None

    @field_validator("quantity", mode="before")
    @classmethod
    def clean_update_quantity(cls, v: object) -> int | None:
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            val = int(v)
            return val if val >= 1 else 1
        except (ValueError, TypeError):
            return None


class ProductImageCreate(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)
    is_primary: bool = False


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    image_url: str
    is_primary: bool
    created_at: datetime


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    description: str | None
    category: str | None
    type: str | None
    artist: str | None
    year: int | None
    material: str | None
    dimensions: str | None
    condition: str | None
    price: float | None = None
    currency: str | None = None
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse] = []
    likes_count: int = 0
    liked_by_me: bool = False
    primary_image: str | None = None
    views: int = 0


class ProductListItem(BaseModel):
    id: int
    owner_id: int | None = None
    title: str
    artist: str | None
    category: str | None
    type: str | None
    primary_image: str | None = None
    likes_count: int = 0
    liked_by_me: bool = False
    views: int = 0
    price: float | None = None
    currency: str | None = None
    created_at: datetime
