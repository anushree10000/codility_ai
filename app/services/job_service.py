from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.job import JobCreate
from app.models.job import Job
from app.models.dead_letter_queue import DeadLetterQueue
from app.repo import job_repo, queue_repo
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.constants import JobStatus
import uuid
from datetime import datetime, timezone

async def create_job(db: AsyncSession, queue_id: str, data: JobCreate, user_id: str) -> Job:
    queue = await queue_repo.get_queue_by_id(db, queue_id)
    if not queue:
        raise NotFoundException("Queue not found")
        
    retry_policy = None
    if queue.retry_policy_id:
        retry_policy = await db.get(queue_repo.RetryPolicy, queue.retry_policy_id)

    max_retries = retry_policy.max_retries if retry_policy else 3

    status = JobStatus.scheduled.value if data.scheduled_at else JobStatus.queued.value

    job = Job(
        id=str(uuid.uuid4()),
        queue_id=queue_id,
        type=data.type,
        status=status,
        priority=data.priority,
        payload=data.payload,
        max_retries=max_retries,
        created_by=user_id,
        batch_id=data.batch_id,
        created_at=datetime.now(timezone.utc),
        scheduled_at=data.scheduled_at
    )
    return await job_repo.create_job(db, job)

async def cancel_job(db: AsyncSession, job_id: str) -> Job:
    job = await job_repo.get_job_by_id(db, job_id)
    if not job:
        raise NotFoundException("Job not found")
        
    if job.status in [JobStatus.running.value, JobStatus.completed.value, JobStatus.cancelled.value, JobStatus.dead_lettered.value]:
        raise BadRequestException(f"Cannot cancel job in {job.status} state")
        
    job.status = JobStatus.cancelled.value
    job.updated_at = datetime.now(timezone.utc)
    return await job_repo.update_job(db, job)

async def retry_job(db: AsyncSession, job_id: str) -> Job:
    job = await job_repo.get_job_by_id(db, job_id)
    if not job:
        raise NotFoundException("Job not found")
        
    if job.status not in [JobStatus.failed.value, JobStatus.dead_lettered.value]:
        raise BadRequestException(f"Cannot retry job in {job.status} state")
        
    job.status = JobStatus.queued.value
    job.attempt_count = 0
    job.worker_id = None
    job.scheduled_at = None
    job.updated_at = datetime.now(timezone.utc)
    return await job_repo.update_job(db, job)

async def requeue_dlq_job(db: AsyncSession, dlq_id: str) -> DeadLetterQueue:
    dlq = await job_repo.get_dlq_entry(db, dlq_id)
    if not dlq:
        raise NotFoundException("DLQ entry not found")
        
    if dlq.requeued_at:
        raise BadRequestException("Job already requeued")
        
    job = await job_repo.get_job_by_id(db, dlq.job_id)
    job.status = JobStatus.queued.value
    job.attempt_count = 0
    job.worker_id = None
    job.updated_at = datetime.now(timezone.utc)
    await job_repo.update_job(db, job)
    
    dlq.requeued_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(dlq)
    return dlq
