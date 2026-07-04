import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeadLetterQueue(Base):
    __tablename__ = "dead_letter_queue"
    __table_args__ = (
        sa.Index("idx_dlq_queue_dead_lettered", "queue_id", "dead_lettered_at"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    queue_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("queues.id"), nullable=False
    )
    failure_reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    total_attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    dead_lettered_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
    requeued_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    job: Mapped["Job"] = relationship()
    queue: Mapped["Queue"] = relationship()
