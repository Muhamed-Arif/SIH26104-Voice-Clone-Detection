import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import AuditLog


class AuditRepository:
    """Data access repository for Audit Logs."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        action: str,
        outcome: str,
        user_id: Optional[uuid.UUID] = None,
        analysis_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        audit_entry = AuditLog(
            audit_id=uuid.uuid4(),
            user_id=user_id,
            analysis_id=analysis_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            action=action,
            outcome=outcome,
        )
        self.db.add(audit_entry)
        await self.db.flush()
        return audit_entry

    async def get_audit_logs(self, limit: int = 50) -> List[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())
