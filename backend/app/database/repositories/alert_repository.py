import uuid
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Alert


class AlertRepository:
    """Data access repository for Alerts."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(
        self,
        analysis_id: uuid.UUID,
        severity: str = "HIGH",
        status: str = "OPEN",
    ) -> Alert:
        alert = Alert(
            alert_id=uuid.uuid4(),
            analysis_id=analysis_id,
            severity=severity,
            status=status,
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def get_alert_by_id(self, alert_id: uuid.UUID) -> Optional[Alert]:
        result = await self.db.execute(
            select(Alert).where(Alert.alert_id == alert_id)
        )
        return result.scalar_one_or_none()

    async def acknowledge_alert(
        self, alert_id: uuid.UUID, acknowledged_by: str
    ) -> Optional[Alert]:
        stmt = (
            update(Alert)
            .where(Alert.alert_id == alert_id)
            .values(status="ACKNOWLEDGED", acknowledged_by=acknowledged_by)
            .returning(Alert)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
