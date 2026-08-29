import asyncio
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.exceptions import ForbiddenError, NotFoundError
from core.websocket_manager import ws_manager
from models.notification import Notification, NotificationType
from models.user import User
from schemas.notification import NotificationCount, NotificationResponse


class NotificationController:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ─── Criar (uso interno por outros controllers) ───────────────────────────

    def create(
        self,
        *,
        user_id: int,
        type: NotificationType,
        title: str,
        body: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type.value,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            is_read=False,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Disparar evento WebSocket em tempo real para o utilizador
        try:
            payload = {
                "event": "new_notification",
                "data": NotificationResponse.model_validate(notification).model_dump(mode="json"),
            }
            # Tentar enviar no loop de eventos ativo
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(ws_manager.send_personal_message(user_id, payload))
            except RuntimeError:
                # Se não houver um loop ativo na thread atual, executa de forma síncrona/direta
                asyncio.run(ws_manager.send_personal_message(user_id, payload))
        except Exception:
            pass  # Não falhar a operação principal caso o websocket apresente erro

        return notification

    # ─── Listar ───────────────────────────────────────────────────────────────

    def list_notifications(
        self,
        user: User,
        *,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NotificationResponse], int]:
        query = select(Notification).where(Notification.user_id == user.id)

        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        notifications = list(
            self.db.scalars(
                query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)
            ).all()
        )

        items = [NotificationResponse.model_validate(n) for n in notifications]
        return items, total

    # ─── Contagem ─────────────────────────────────────────────────────────────

    def get_count(self, user: User) -> NotificationCount:
        total = self.db.scalar(
            select(func.count()).where(Notification.user_id == user.id)
        ) or 0
        unread = self.db.scalar(
            select(func.count()).where(
                Notification.user_id == user.id,
                Notification.is_read == False,  # noqa: E712
            )
        ) or 0
        return NotificationCount(unread=unread, total=total)

    # ─── Marcar como lida ─────────────────────────────────────────────────────

    def mark_read(self, user: User, notification_id: int) -> NotificationResponse:
        notification = self.db.scalar(
            select(Notification).where(Notification.id == notification_id)
        )
        if notification is None:
            raise NotFoundError("Notificação não encontrada")
        if notification.user_id != user.id:
            raise ForbiddenError("Sem permissão para aceder a esta notificação")

        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return NotificationResponse.model_validate(notification)

    def mark_all_read(self, user: User) -> int:
        """Marca todas as notificações não lidas como lidas. Retorna o número actualizado."""
        notifications = list(
            self.db.scalars(
                select(Notification).where(
                    Notification.user_id == user.id,
                    Notification.is_read == False,  # noqa: E712
                )
            ).all()
        )
        for n in notifications:
            n.is_read = True
        self.db.commit()
        return len(notifications)
