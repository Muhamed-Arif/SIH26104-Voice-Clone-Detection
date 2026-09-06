import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import AnalysisEvent, ModelRegistry, RiskLevel


class AnalysisRepository:
    """Data access repository for Analysis Events and Model Registry."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_model_version(self, version: str) -> ModelRegistry:
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.version == version)
        )
        model = result.scalar_one_or_none()
        if not model:
            model = ModelRegistry(
                version=version,
                metrics={"accuracy": 0.94, "f1_score": 0.92},
                threshold=0.70,
                status="active",
            )
            self.db.add(model)
            await self.db.flush()
        return model

    async def create_analysis_event(
        self,
        analysis_id: uuid.UUID,
        session_id: uuid.UUID,
        chunk_id: str,
        synthetic_probability: float,
        confidence: float,
        risk_score: int,
        risk_level: RiskLevel,
        audio_quality: str = "HIGH",
        action: str = "ALLOW",
        latency_ms: float = 0.0,
        model_version: str = "v0.3",
    ) -> AnalysisEvent:
        await self.ensure_model_version(model_version)
        event = AnalysisEvent(
            analysis_id=analysis_id,
            session_id=session_id,
            chunk_id=chunk_id,
            synthetic_probability=synthetic_probability,
            confidence=confidence,
            risk_score=risk_score,
            risk_level=risk_level,
            audio_quality=audio_quality,
            action=action,
            latency_ms=latency_ms,
            model_version=model_version,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_analysis_by_id(self, analysis_id: uuid.UUID) -> Optional[AnalysisEvent]:
        result = await self.db.execute(
            select(AnalysisEvent)
            .options(selectinload(AnalysisEvent.alerts))
            .where(AnalysisEvent.analysis_id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_session_events(
        self, session_id: uuid.UUID, limit: int = 100
    ) -> List[AnalysisEvent]:
        result = await self.db.execute(
            select(AnalysisEvent)
            .where(AnalysisEvent.session_id == session_id)
            .order_by(AnalysisEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
