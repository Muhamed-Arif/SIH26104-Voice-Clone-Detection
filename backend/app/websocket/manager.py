import uuid
from typing import Dict, List, Set
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket client connections organized by session."""

    def __init__(self):
        # Map session_id -> list of connected WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket client connected to session {session_id}. Active: {len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket client disconnected from session {session_id}")

    async def send_personal_json(self, data: dict, websocket: WebSocket) -> None:
        await websocket.send_json(data)

    async def broadcast_to_session(self, data: dict, session_id: str) -> None:
        if session_id in self.active_connections:
            for connection in list(self.active_connections[session_id]):
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket in session {session_id}: {e}")


ws_manager = ConnectionManager()
