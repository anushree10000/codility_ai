from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class RetryPolicyBase(BaseModel):
    name: str
    strategy: str
    max_retries: int = 3
    base_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    jitter: bool = True

class RetryPolicyCreate(RetryPolicyBase):
    pass

class RetryPolicyResponse(RetryPolicyBase):
    id: uuid.UUID | str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QueueBase(BaseModel):
    name: str
    slug: str
    priority: int = 0
    concurrency_limit: int = 5
    retry_policy_id: uuid.UUID | str | None = None
    is_paused: bool = False
    max_job_duration_seconds: int = 3600

class QueueCreate(QueueBase):
    pass

class QueueUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    concurrency_limit: int | None = None
    retry_policy_id: uuid.UUID | str | None = None
    is_paused: bool | None = None
    max_job_duration_seconds: int | None = None

class QueueResponse(QueueBase):
    id: uuid.UUID | str
    project_id: uuid.UUID | str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
