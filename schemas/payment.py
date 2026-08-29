from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethod(str, Enum):
    MPESA = "mpesa"
    EMOLA = "emola"
    MKESH = "mkesh"
    PAYPAL = "paypal"
    SKYWALLET = "skywallet"
    CASH = "cash"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentCreate(BaseModel):
    order_id: int
    method: PaymentMethod
    provider: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: float
    currency: str
    method: str
    provider: str | None
    transaction_id: str | None
    status: str
    paid_at: datetime | None
    created_at: datetime
