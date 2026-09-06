import time
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundException, InvalidAudioChunkException
from app.core.logging import get_logger
from app.database.base import RiskLevel
from app.database.repositories.session_repository import SessionRepository
from app.database.repositories.analysis_repository import AnalysisRepository
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.audit_repository import AuditRepository
from app.risk_engine.risk_calculator import RiskCalculator
from app.schemas.audio import DSPAudioChunk
from app.schemas.analysis import AnalysisResultResponse, AlertResponse
from app.services.ml_client import MLClient
from app.services.prevention_adapter import PreventionAdapter

logger = get_logger(__name__)


class AudioOrchestrator:
    """Coordinates audio chunk analysis pipeline across ML, Risk Engine, Persistence, and Prevention."""

    def __init__(self, db: AsyncSession, ml_client: Optional[MLClient] = None):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.alert_repo = AlertRepository(db)
        self.audit_repo = AuditRepository(db)
        self.ml_client = ml_client or MLClient()

    async def process_chunk(
        self,
        chunk: DSPAudioChunk,
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> AnalysisResultResponse:
        start_time = time.perf_counter()

        # 1. Resolve or validate session
        effective_session_id = session_id or chunk.session_id
        if not effective_session_id:
            # Auto-provision a default session if not provided
            default_user_id = user_id or uuid.uuid4()
            effective_session_id = uuid.uuid4()
            await self.session_repo.create_session(
                session_id=effective_session_id,
                user_id=default_user_id,
                mode="realtime",
                status="active",
            )
        else:
            session = await self.session_repo.get_session_by_id(effective_session_id)
            if not session:
                default_user_id = user_id or uuid.uuid4()
                await self.session_repo.create_session(
                    session_id=effective_session_id,
                    user_id=default_user_id,
                    mode="realtime",
                    status="active",
                )

        # 2. Invoke ML Client
        ml_prediction = await self.ml_client.predict(chunk)

        # 3. Calculate Risk with Risk Engine
        risk_assessment = RiskCalculator.calculate_risk(
            synthetic_probability=ml_prediction.synthetic_probability,
            confidence=ml_prediction.confidence,
            audio_quality=chunk.quality,
        )

        # Latency measurement
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        analysis_id = uuid.uuid4()

        # 4. Persist Analysis Event
        analysis_event = await self.analysis_repo.create_analysis_event(
            analysis_id=analysis_id,
            session_id=effective_session_id,
            chunk_id=chunk.chunk_id,
            synthetic_probability=ml_prediction.synthetic_probability,
            confidence=ml_prediction.confidence,
            risk_score=risk_assessment.risk_score,
            risk_level=risk_assessment.risk_level,
            audio_quality=chunk.quality,
            action=risk_assessment.suggested_action,
            latency_ms=elapsed_ms,
            model_version=ml_prediction.model_version,
        )

        # 5. Handle HIGH Risk Alert & Prevention
        alert_response: Optional[AlertResponse] = None
        if risk_assessment.risk_level == RiskLevel.HIGH:
            alert = await self.alert_repo.create_alert(
                analysis_id=analysis_id,
                severity="HIGH",
                status="OPEN",
            )
            alert_response = AlertResponse.model_validate(alert)

            # Trigger downstream prevention
            await PreventionAdapter.trigger_prevention(
                session_id=effective_session_id,
                analysis_id=analysis_id,
                risk_score=risk_assessment.risk_score,
                reason_codes=risk_assessment.reason_codes,
            )

        # 6. Record Audit Log
        outcome = "FLAGGED_HIGH_RISK" if risk_assessment.risk_level == RiskLevel.HIGH else "PROCESSED_NORMAL"
        await self.audit_repo.log_event(
            event_type="AUDIO_CHUNK_ANALYZED",
            action=f"ANALYZE_{risk_assessment.suggested_action}",
            outcome=outcome,
            user_id=user_id,
            analysis_id=analysis_id,
        )

        return AnalysisResultResponse(
            analysis_id=analysis_event.analysis_id,
            session_id=analysis_event.session_id,
            chunk_id=analysis_event.chunk_id,
            synthetic_probability=analysis_event.synthetic_probability,
            confidence=analysis_event.confidence,
            risk_score=analysis_event.risk_score,
            risk_level=analysis_event.risk_level,
            audio_quality=analysis_event.audio_quality,
            action=analysis_event.action,
            latency_ms=analysis_event.latency_ms,
            model_version=analysis_event.model_version,
            created_at=analysis_event.created_at,
            reason_codes=risk_assessment.reason_codes,
            risk_factors=risk_assessment.risk_factors,
            alert=alert_response,
        )
