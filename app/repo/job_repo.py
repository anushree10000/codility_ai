from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.job_log import JobLog
from app.models.dead_letter_queue import DeadLetterQueue
from app.models.queue import Queue
from typing import Sequence

async def create_job(db: AsyncSession, job: Job) -> Job:
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job

async def get_job_by_id(db: AsyncSession, job_id: str) -> Job | None:
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_queue_jobs(db: AsyncSession, queue_id: str, skip: int = 0, limit: int = 20) -> Sequence[Job]:
    stmt = select(Job).where(Job.queue_id == queue_id).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_job(db: AsyncSession, job: Job) -> Job:
    await db.flush()
    await db.refresh(job)
    return job

async def claim_next_job(db: AsyncSession, queue_id: str, worker_id: str) -> Job | None:
    # Check queue concurrency limit
    queue_stmt = select(Queue.concurrency_limit).where(Queue.id == queue_id)
    concurrency_limit = (await db.execute(queue_stmt)).scalar_one_or_none()
    if concurrency_limit is None:
        return None
        
    running_count_stmt = select(func.count(Job.id)).where(Job.queue_id == queue_id, Job.status == "running")
    running_count = (await db.execute(running_count_stmt)).scalar() or 0
    
    if running_count >= concurrency_limit:
        return None

    # Atomic job claim using SKIP LOCKED
    stmt = (
        select(Job)
        .where(
            Job.queue_id == queue_id,
            Job.status.in_(["queued", "scheduled"]),
            or_(Job.scheduled_at.is_(None), Job.scheduled_at <= func.now())
        )
        .order_by(Job.priority.desc(), Job.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        return None

    job.status = "claimed"
    job.worker_id = worker_id
    job.claimed_at = func.now()
    
    await db.flush()
    return job

async def create_job_execution(db: AsyncSession, execution: JobExecution) -> JobExecution:
    db.add(execution)
    await db.flush()
    await db.refresh(execution)
    return execution

async def get_job_executions(db: AsyncSession, job_id: str) -> Sequence[JobExecution]:
    stmt = select(JobExecution).where(JobExecution.job_id == job_id).order_by(JobExecution.attempt_number.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_job_log(db: AsyncSession, log: JobLog) -> JobLog:
    db.add(log)
    await db.flush()
    return log

async def get_job_logs(db: AsyncSession, job_id: str) -> Sequence[JobLog]:
    stmt = select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.timestamp.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_dlq_entry(db: AsyncSession, dlq: DeadLetterQueue) -> DeadLetterQueue:
    db.add(dlq)
    await db.flush()
    return dlq

async def get_queue_dlq(db: AsyncSession, queue_id: str) -> Sequence[DeadLetterQueue]:
    stmt = select(DeadLetterQueue).where(DeadLetterQueue.queue_id == queue_id).order_by(DeadLetterQueue.dead_lettered_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_dlq_entry(db: AsyncSession, dlq_id: str) -> DeadLetterQueue | None:
    stmt = select(DeadLetterQueue).where(DeadLetterQueue.id == dlq_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
