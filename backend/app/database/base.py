import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative Base class for SQLAlchemy models."""
    pass


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    role: Mapped[str] = mapped_column(String(50), default="analyst", nullable=False)
    auth_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
    )

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    mode: Mapped[str] = mapped_column(String(50), default="realtime", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    analysis_events: Mapped[List["AnalysisEvent"]] = relationship(
        "AnalysisEvent", back_populates="session", cascade="all, delete-orphan"
    )


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, default=0.70, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Relationships
    analysis_events: Mapped[List["AnalysisEvent"]] = relationship(
        "AnalysisEvent", back_populates="model_ref"
    )


class AnalysisEvent(Base):
    __tablename__ = "analysis_events"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    synthetic_probability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    audio_quality: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    action: Mapped[str] = mapped_column(String(50), default="ALLOW", nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    model_version: Mapped[str] = mapped_column(
        ForeignKey("model_registry.version", ondelete="SET NULL"),
        nullable=True,
        default="v0.3",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
        index=True,
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="analysis_events")
    model_ref: Mapped[Optional["ModelRegistry"]] = relationship(
        "ModelRegistry", back_populates="analysis_events"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="analysis_event", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="analysis_event"
    )


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_events.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
    )

    # Relationships
    analysis_event: Mapped["AnalysisEvent"] = relationship("AnalysisEvent", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("analysis_events.analysis_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    analysis_event: Mapped[Optional["AnalysisEvent"]] = relationship(
        "AnalysisEvent", back_populates="audit_logs"
    )
