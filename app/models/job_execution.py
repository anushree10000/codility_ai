import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobExecution(Base):
    __tablename__ = "job_executions"
    __table_args__ = (
        sa.Index("idx_job_executions_job_attempt", "job_id", "attempt_number"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    worker_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("workers.id"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Enum("running", "completed", "failed", "timed_out", name="execution_status"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="executions")
    worker: Mapped["Worker"] = relationship()
