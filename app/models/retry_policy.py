import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id: Mapped[str] = mapped_column(
        sa.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(
        sa.Enum("fixed", "linear", "exponential", name="retry_strategy"), nullable=False
    )
    max_retries: Mapped[int] = mapped_column(sa.Integer, default=3, nullable=False)
    base_delay_seconds: Mapped[int] = mapped_column(sa.Integer, default=60, nullable=False)
    max_delay_seconds: Mapped[int] = mapped_column(sa.Integer, default=3600, nullable=False)
    jitter: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )
