from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class WorkerResponse(BaseModel):
    id: uuid.UUID | str
    hostname: str
    pid: int
    queue_id: uuid.UUID | str | None = None
    status: str
    concurrency: int
    active_jobs: int
    registered_at: datetime
    last_heartbeat_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkerHeartbeatResponse(BaseModel):
    id: int
    worker_id: uuid.UUID | str
    active_jobs: int
    cpu_usage: float | None = None
    memory_usage: float | None = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
