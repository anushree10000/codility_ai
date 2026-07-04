from enum import Enum


class OrgRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class JobType(str, Enum):
    immediate = "immediate"
    delayed = "delayed"
    scheduled = "scheduled"
    recurring = "recurring"
    batch = "batch"


class JobStatus(str, Enum):
    queued = "queued"
    scheduled = "scheduled"
    claimed = "claimed"
    running = "running"
    completed = "completed"
    failed = "failed"
    dead_lettered = "dead_lettered"
    cancelled = "cancelled"


class WorkerStatus(str, Enum):
    online = "online"
    busy = "busy"
    draining = "draining"
    offline = "offline"


class ExecutionStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"
    timed_out = "timed_out"


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"


class RetryStrategy(str, Enum):
    fixed = "fixed"
    linear = "linear"
    exponential = "exponential"
