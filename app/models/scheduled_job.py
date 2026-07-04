import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"
    __table_args__ = (
        sa.Index("idx_scheduled_jobs_active_next", "is_active", "next_run_at"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    queue_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("queues.id", ondelete="CASCADE"), nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    payload: Mapped[Any] = mapped_column(sa.JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )

    queue: Mapped["Queue"] = relationship(back_populates="scheduled_jobs")
    creator: Mapped["User"] = relationship()
