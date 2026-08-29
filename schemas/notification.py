from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Resposta de uma notificação."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    body: str | None
    entity_type: str | None
    entity_id: int | None
    is_read: bool
    created_at: datetime


class NotificationCount(BaseModel):
    """Contador de notificações não lidas."""

    unread: int
    total: int
