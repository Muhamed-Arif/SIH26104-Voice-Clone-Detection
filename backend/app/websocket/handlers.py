import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.schemas.audio import DSPAudioChunk
from app.security.validation import validate_dsp_chunk
from app.services.audio_orchestrator import AudioOrchestrator
from app.websocket.manager import ws_manager

logger = get_logger(__name__)


async def handle_stream_connection(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Processes real-time audio chunk stream over WebSocket."""
    str_session_id = str(session_id)
    await ws_manager.connect(websocket, str_session_id)
    orchestrator = AudioOrchestrator(db)

    try:
        # Acknowledge connection
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "session_id": str_session_id,
            "status": "READY",
        })

        while True:
            raw_data = await websocket.receive_text()
            try:
                message_json = json.loads(raw_data)
            except Exception:
                await websocket.send_json({
                    "type": "ERROR",
                    "error": {"code": "INVALID_JSON", "message": "Malformed JSON payload in stream frame"},
                })
                continue

            # Heartbeat ping handling
            if message_json.get("type") == "PING":
                await websocket.send_json({"type": "PONG", "timestamp": message_json.get("timestamp")})
                continue

            # Process chunk frame
            try:
                # If frame is wrapped in a type or is directly the DSP chunk
                chunk_data = message_json.get("chunk", message_json)
                chunk_obj = DSPAudioChunk.model_validate(chunk_data)
                validate_dsp_chunk(chunk_obj)

                # Execute pipeline
                result = await orchestrator.process_chunk(
                    chunk=chunk_obj,
                    session_id=session_id,
                )

                # Send analysis frame back over WebSocket
                result_payload = {
                    "type": "ANALYSIS_RESULT",
                    "data": result.model_dump(mode="json"),
                }
                await ws_manager.send_personal_json(result_payload, websocket)

            except Exception as exc:
                logger.error(f"Error processing stream chunk for session {str_session_id}: {exc}")
                await websocket.send_json({
                    "type": "ERROR",
                    "error": {
                        "code": "CHUNK_PROCESSING_ERROR",
                        "message": str(exc),
                    },
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, str_session_id)
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
        ws_manager.disconnect(websocket, str_session_id)
