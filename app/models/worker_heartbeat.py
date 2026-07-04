from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    __table_args__ = (
        sa.Index("idx_worker_heartbeats_worker_ts", "worker_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, primary_key=True, autoincrement=True
    )
    worker_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False
    )
    active_jobs: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    cpu_usage: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )

    worker: Mapped["Worker"] = relationship(back_populates="heartbeats")
