import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Queue(Base):
    __tablename__ = "queues"
    __table_args__ = (
        sa.UniqueConstraint("project_id", "slug", name="uq_queues_project_slug"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    priority: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    concurrency_limit: Mapped[int] = mapped_column(sa.Integer, default=5, nullable=False)
    retry_policy_id: Mapped[Optional[str]] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("retry_policies.id"), nullable=True
    )
    is_paused: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    max_job_duration_seconds: Mapped[int] = mapped_column(
        sa.Integer, default=3600, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="queues")
    retry_policy: Mapped[Optional["RetryPolicy"]] = relationship()
    jobs: Mapped[list["Job"]] = relationship(back_populates="queue")
    scheduled_jobs: Mapped[list["ScheduledJob"]] = relationship(back_populates="queue")
