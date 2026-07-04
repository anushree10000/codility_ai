import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        sa.Index("idx_jobs_claimable", "queue_id", "status", "scheduled_at", "priority"),
        sa.Index("idx_jobs_batch", "batch_id"),
        sa.Index("idx_jobs_status", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    queue_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("queues.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        sa.Enum(
            "immediate", "delayed", "scheduled", "recurring", "batch",
            name="job_type",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.Enum(
            "queued", "scheduled", "claimed", "running", "completed",
            "failed", "dead_lettered", "cancelled",
            name="job_status",
        ),
        default="queued",
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    payload: Mapped[Any] = mapped_column(sa.JSON, nullable=False)
    result: Mapped[Optional[Any]] = mapped_column(sa.JSON, nullable=True)
    attempt_count: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(sa.Integer, default=3, nullable=False)
    created_by: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("users.id"), nullable=False
    )
    worker_id: Mapped[Optional[str]] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("workers.id"), nullable=True
    )
    batch_id: Mapped[Optional[str]] = mapped_column(sa.CHAR(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    queue: Mapped["Queue"] = relationship(back_populates="jobs")
    creator: Mapped["User"] = relationship()
    worker: Mapped[Optional["Worker"]] = relationship()
    executions: Mapped[list["JobExecution"]] = relationship(back_populates="job")
    logs: Mapped[list["JobLog"]] = relationship(back_populates="job")
