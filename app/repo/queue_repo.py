from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy
from app.schemas.queue import QueueUpdate

async def get_queue_by_slug(db: AsyncSession, project_id: str, slug: str) -> Queue | None:
    stmt = select(Queue).where(Queue.project_id == project_id, Queue.slug == slug)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_queue(db: AsyncSession, queue: Queue) -> Queue:
    db.add(queue)
    await db.flush()
    await db.refresh(queue)
    return queue

async def get_project_queues(db: AsyncSession, project_id: str) -> list[Queue]:
    stmt = select(Queue).where(Queue.project_id == project_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_queue_by_id(db: AsyncSession, queue_id: str) -> Queue | None:
    stmt = select(Queue).where(Queue.id == queue_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_queue(db: AsyncSession, queue: Queue, data: QueueUpdate) -> Queue:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(queue, key, value)
    await db.flush()
    await db.refresh(queue)
    return queue

async def create_retry_policy(db: AsyncSession, policy: RetryPolicy) -> RetryPolicy:
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return policy

async def get_retry_policies(db: AsyncSession) -> list[RetryPolicy]:
    stmt = select(RetryPolicy)
    result = await db.execute(stmt)
    return list(result.scalars().all())
