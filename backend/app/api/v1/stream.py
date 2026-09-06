import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.websocket.handlers import handle_stream_connection

router = APIRouter(tags=["Streaming"])


@router.websocket("/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    session_id: Optional[uuid.UUID] = Query(None, description="Active session UUID for the stream"),
    db: AsyncSession = Depends(get_db),
):
    """Real-time bi-directional WebSocket audio stream pipeline."""
    target_session_id = session_id or uuid.uuid4()
    await handle_stream_connection(
        websocket=websocket,
        session_id=target_session_id,
        db=db,
    )
