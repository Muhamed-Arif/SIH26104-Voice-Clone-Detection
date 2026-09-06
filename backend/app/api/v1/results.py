import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisResultResponse, AlertResponse
from app.schemas.errors import ErrorResponse
from app.services.result_aggregator import ResultAggregator

router = APIRouter(prefix="/results", tags=["Results"])


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResultResponse,
    summary="Get detailed analysis event by ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_analysis_result(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResultResponse:
    """Fetches a single analysis event including synthetic probability, risk score, and alert if generated."""
    repo = AnalysisRepository(db)
    event = await repo.get_analysis_by_id(analysis_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis event with id '{analysis_id}' was not found.",
        )

    alert_resp = AlertResponse.model_validate(event.alerts[0]) if event.alerts else None

    return AnalysisResultResponse(
        analysis_id=event.analysis_id,
        session_id=event.session_id,
        chunk_id=event.chunk_id,
        synthetic_probability=event.synthetic_probability,
        confidence=event.confidence,
        risk_score=event.risk_score,
        risk_level=event.risk_level,
        audio_quality=event.audio_quality,
        action=event.action,
        latency_ms=event.latency_ms,
        model_version=event.model_version,
        created_at=event.created_at,
        reason_codes=[],
        alert=alert_resp,
    )


@router.get(
    "/session/{session_id}/aggregate",
    summary="Get aggregated risk metrics for a session",
    responses={404: {"model": ErrorResponse}},
)
async def get_session_aggregate(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Computes session-level aggregate metrics over all processed chunks."""
    aggregator = ResultAggregator(db)
    return await aggregator.aggregate_session_metrics(session_id)
