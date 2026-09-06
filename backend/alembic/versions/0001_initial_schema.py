"""Initial schema creation for SIH26104

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-05 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="analyst"),
        sa.Column("auth_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. sessions table
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mode", sa.String(length=50), nullable=False, server_default="realtime"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    # 3. model_registry table
    op.create_table(
        "model_registry",
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False, server_default="0.70"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("model_id"),
        sa.UniqueConstraint("version"),
    )

    # 4. analysis_events table
    op.create_table(
        "analysis_events",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.String(length=100), nullable=False),
        sa.Column("synthetic_probability", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("audio_quality", sa.String(length=50), nullable=False, server_default="HIGH"),
        sa.Column("action", sa.String(length=50), nullable=False, server_default="ALLOW"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_version"], ["model_registry.version"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("analysis_id"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_analysis_events_session_id"), "analysis_events", ["session_id"], unique=False)
    op.create_index(op.f("ix_analysis_events_chunk_id"), "analysis_events", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_analysis_events_risk_level"), "analysis_events", ["risk_level"], unique=False)
    op.create_index(op.f("ix_analysis_events_created_at"), "analysis_events", ["created_at"], unique=False)

    # 5. alerts table
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="HIGH"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="OPEN"),
        sa.Column("acknowledged_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_events.analysis_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("alert_id"),
    )
    op.create_index(op.f("ix_alerts_analysis_id"), "alerts", ["analysis_id"], unique=False)

    # 6. audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("analysis_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("outcome", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_events.analysis_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_analysis_id"), "audit_logs", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("analysis_events")
    op.drop_table("model_registry")
    op.drop_table("sessions")
    op.drop_table("users")
