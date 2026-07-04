from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid
from typing import Any

class JobCreate(BaseModel):
    type: str
    priority: int = 0
    payload: dict[str, Any]
    scheduled_at: datetime | None = None
    batch_id: uuid.UUID | str | None = None

class JobResponse(BaseModel):
    id: uuid.UUID | str
    queue_id: uuid.UUID | str
    type: str
    status: str
    priority: int
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    attempt_count: int
    max_retries: int
    created_by: uuid.UUID | str | None = None
    worker_id: uuid.UUID | str | None = None
    batch_id: uuid.UUID | str | None = None
    created_at: datetime
    scheduled_at: datetime | None = None
    claimed_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class JobExecutionResponse(BaseModel):
    id: uuid.UUID | str
    job_id: uuid.UUID | str
    worker_id: uuid.UUID | str | None = None
    attempt_number: int
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    error_traceback: str | None = None
    model_config = ConfigDict(from_attributes=True)

class JobLogResponse(BaseModel):
    id: int
    job_id: uuid.UUID | str
    execution_id: uuid.UUID | str | None = None
    level: str
    message: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class DLQResponse(BaseModel):
    id: uuid.UUID | str
    job_id: uuid.UUID | str
    queue_id: uuid.UUID | str
    failure_reason: str
    last_error: str | None = None
    total_attempts: int
    dead_lettered_at: datetime
    requeued_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
