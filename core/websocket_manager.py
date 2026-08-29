import asyncio
from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        # Mapeia user_id -> lista de WebSockets ativos (um utilizador pode estar conectado em vários dispositivos)
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, user_id: int, message: dict[str, Any]) -> None:
        """Envia mensagem JSON para todas as conexões ativas do utilizador."""
        if user_id not in self.active_connections:
            return

        dead_sockets: list[WebSocket] = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_sockets.append(connection)

        for dead in dead_sockets:
            self.disconnect(dead, user_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Envia mensagem para todas as conexões de todos os utilizadores."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(user_id, message)


# Instância global do gestor de WebSockets
ws_manager = WebSocketManager()
