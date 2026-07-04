from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobLog(Base):
    __tablename__ = "job_logs"
    __table_args__ = (
        sa.Index("idx_job_logs_job_timestamp", "job_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, primary_key=True, autoincrement=True
    )
    job_id: Mapped[str] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    execution_id: Mapped[Optional[str]] = mapped_column(
        sa.CHAR(36), sa.ForeignKey("job_executions.id"), nullable=True
    )
    level: Mapped[str] = mapped_column(
        sa.Enum("debug", "info", "warn", "error", name="log_level"), nullable=False
    )
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="logs")
    execution: Mapped[Optional["JobExecution"]] = relationship()
