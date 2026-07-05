from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.queue import QueueCreate, QueueUpdate, RetryPolicyCreate
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy
from app.repo import queue_repo
from app.core.exceptions import ConflictException, NotFoundException
import uuid
from datetime import datetime, timezone

async def create_retry_policy(db: AsyncSession, data: RetryPolicyCreate) -> RetryPolicy:
    policy = RetryPolicy(
        id=str(uuid.uuid4()),
        name=data.name,
        strategy=data.strategy,
        max_retries=data.max_retries,
        base_delay_seconds=data.base_delay_seconds,
        max_delay_seconds=data.max_delay_seconds,
        jitter=data.jitter,
        created_at=datetime.now(timezone.utc)
    )
    return await queue_repo.create_retry_policy(db, policy)

async def create_queue(db: AsyncSession, project_id: str, data: QueueCreate) -> Queue:
    existing = await queue_repo.get_queue_by_slug(db, project_id, data.slug)
    if existing:
        raise ConflictException("Queue slug already exists in this project")

    queue = Queue(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=data.name,
        slug=data.slug,
        priority=data.priority,
        concurrency_limit=data.concurrency_limit,
        retry_policy_id=data.retry_policy_id,
        is_paused=data.is_paused,
        max_job_duration_seconds=data.max_job_duration_seconds,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    return await queue_repo.create_queue(db, queue)

async def get_queue_or_404(db: AsyncSession, queue_id: str) -> Queue:
    queue = await queue_repo.get_queue_by_id(db, queue_id)
    if not queue:
        raise NotFoundException("Queue not found")
    return queue

async def update_queue(db: AsyncSession, queue_id: str, data: QueueUpdate) -> Queue:
    queue = await get_queue_or_404(db, queue_id)
    return await queue_repo.update_queue(db, queue, data)

async def set_queue_pause_state(db: AsyncSession, queue_id: str, is_paused: bool) -> Queue:
    queue = await get_queue_or_404(db, queue_id)
    queue.is_paused = is_paused
    queue.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(queue)
    return queue
