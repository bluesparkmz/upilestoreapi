from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from controllers.notification_controller import NotificationController
from core.database import get_db
from core.websocket_manager import ws_manager
from dependencies.auth import get_user_from_token

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: Annotated[str | None, Query(description="Token de acesso JWT")] = None,
    db: Session = Depends(get_db),
) -> None:
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token ausente")
        return

    user = get_user_from_token(token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido ou expirado")
        return

    await ws_manager.connect(websocket, user.id)

    # Obter contagem inicial de notificações não lidas
    try:
        count = NotificationController(db).get_count(user)
        await websocket.send_json(
            {
                "event": "connected",
                "data": {
                    "message": "Conectado ao canal de notificações em tempo real",
                    "unread_count": count.unread,
                    "total_count": count.total,
                },
            }
        )

        while True:
            # Escutar mensagens do cliente (ex: ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user.id)
    except Exception:
        ws_manager.disconnect(websocket, user.id)
