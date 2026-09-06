import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories.analysis_repository import AnalysisRepository
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.audit_repository import AuditRepository
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.schemas.errors import ErrorResponse
from app.security.authentication import get_current_user_optional

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.post(
    "",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit manual verification or override for an analysis event",
    responses={404: {"model": ErrorResponse}},
)
async def verify_analysis(
    payload: VerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
) -> VerificationResponse:
    """Logs an analyst's manual review decision and updates associated alert state."""
    analysis_repo = AnalysisRepository(db)
    alert_repo = AlertRepository(db)
    audit_repo = AuditRepository(db)

    # 1. Verify analysis event exists
    event = await analysis_repo.get_analysis_by_id(payload.analysis_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis event with id '{payload.analysis_id}' was not found.",
        )

    # 2. Acknowledge alert if present
    if event.alerts:
        verifier_name = str(payload.verifier_id or "analyst")
        for alert in event.alerts:
            await alert_repo.acknowledge_alert(alert.alert_id, acknowledged_by=verifier_name)

    # 3. Log audit event
    user_id = payload.verifier_id or (current_user.get("user_id") if current_user else None)
    audit_entry = await audit_repo.log_event(
        event_type="MANUAL_VERIFICATION_SUBMITTED",
        action=f"VERIFY_{payload.decision}",
        outcome="VERIFIED",
        user_id=user_id,
        analysis_id=payload.analysis_id,
    )

    return VerificationResponse(
        status="SUCCESS",
        analysis_id=payload.analysis_id,
        decision=payload.decision,
        verified_at=datetime.now(timezone.utc).isoformat(),
        audit_id=audit_entry.audit_id,
    )
