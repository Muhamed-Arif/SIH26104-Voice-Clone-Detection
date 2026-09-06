import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.audio import DSPAudioChunk
from app.schemas.analysis import AnalysisResultResponse
from app.schemas.errors import ErrorResponse
from app.security.validation import validate_dsp_chunk
from app.security.rate_limit import check_rate_limit
from app.security.authentication import get_current_user_optional
from app.services.audio_orchestrator import AudioOrchestrator

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_rate_limit)],
    summary="Analyze a DSP audio chunk for synthetic voice clone artifacts",
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def analyze_chunk(
    chunk: DSPAudioChunk,
    x_session_id: Optional[uuid.UUID] = Header(None, description="Optional Session ID in Header"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
) -> AnalysisResultResponse:
    """Processes an incoming DSP waveform chunk through the ML inference client,

    risk calculation engine, and persistence layer. Flags HIGH risk events automatically.
    """
    # 1. Validate payload
    validate_dsp_chunk(chunk)

    user_id = current_user.get("user_id") if current_user else None
    effective_session_id = x_session_id or chunk.session_id

    # 2. Orchestrate pipeline
    orchestrator = AudioOrchestrator(db)
    result = await orchestrator.process_chunk(
        chunk=chunk,
        session_id=effective_session_id,
        user_id=user_id,
    )
    return result
