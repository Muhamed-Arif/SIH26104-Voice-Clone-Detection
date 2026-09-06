import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundException
from app.core.logging import get_logger
from app.database.base import Session
from app.database.repositories.session_repository import SessionRepository
from app.database.repositories.audit_repository import AuditRepository

logger = get_logger(__name__)


class SessionManager:
    """Manages audio analysis session lifecycles."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_session(
        self,
        user_id: uuid.UUID,
        mode: str = "realtime",
        session_id: Optional[uuid.UUID] = None,
    ) -> Session:
        sid = session_id or uuid.uuid4()
        session = await self.session_repo.create_session(
            session_id=sid,
            user_id=user_id,
            mode=mode,
            status="active",
        )
        await self.audit_repo.log_event(
            event_type="SESSION_CREATED",
            action="CREATE",
            outcome="SUCCESS",
            user_id=user_id,
        )
        logger.info(f"Created new session {sid} for user {user_id} with mode {mode}")
        return session

    async def get_session(self, session_id: uuid.UUID) -> Session:
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise EntityNotFoundException(entity="Session", identifier=session_id)
        return session

    async def close_session(
        self, session_id: uuid.UUID, status: str = "completed"
    ) -> Session:
        session = await self.session_repo.close_session(session_id, status=status)
        if not session:
            raise EntityNotFoundException(entity="Session", identifier=session_id)
        await self.audit_repo.log_event(
            event_type="SESSION_CLOSED",
            action="CLOSE",
            outcome="SUCCESS",
            user_id=session.user_id,
        )
        logger.info(f"Closed session {session_id} with status {status}")
        return session
