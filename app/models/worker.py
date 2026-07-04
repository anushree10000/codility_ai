import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Worker(Base):
    __tablename__ = "workers"
    __table_args__ = (
        sa.Index("idx_workers_status_heartbeat", "status", "last_heartbeat_at"),
    )

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    hostname: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    pid: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    queue_id: Mapped[Optional[str]] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("queues.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        sa.Enum("online", "busy", "draining", "offline", name="worker_status"),
        nullable=False,
    )
    concurrency: Mapped[int] = mapped_column(sa.Integer, default=5, nullable=False)
    active_jobs: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )

    queue: Mapped[Optional["Queue"]] = relationship()
    heartbeats: Mapped[list["WorkerHeartbeat"]] = relationship(back_populates="worker")
