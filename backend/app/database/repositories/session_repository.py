import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Session, User


class SessionRepository:
    """Data access repository for Sessions and Users."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(
        self, user_id: uuid.UUID, role: str = "analyst", auth_metadata: Optional[dict] = None
    ) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=user_id,
                role=role,
                auth_metadata=auth_metadata or {},
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(user)
            await self.db.flush()
        return user

    async def create_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        mode: str = "realtime",
        status: str = "active",
    ) -> Session:
        await self.get_or_create_user(user_id)
        session = Session(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(timezone.utc),
            mode=mode,
            status=status,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        result = await self.db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def close_session(self, session_id: uuid.UUID, status: str = "completed") -> Optional[Session]:
        stmt = (
            update(Session)
            .where(Session.session_id == session_id)
            .values(end_time=datetime.now(timezone.utc), status=status)
            .returning(Session)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
