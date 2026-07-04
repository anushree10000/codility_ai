from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.worker import Worker
from app.models.worker_heartbeat import WorkerHeartbeat
from typing import Sequence

from datetime import datetime, timezone, timedelta

async def get_all_workers(db: AsyncSession) -> Sequence[Worker]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    stmt = select(Worker).where(Worker.last_heartbeat_at >= cutoff).order_by(Worker.registered_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_worker_by_id(db: AsyncSession, worker_id: str) -> Worker | None:
    stmt = select(Worker).where(Worker.id == worker_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_worker_heartbeats(db: AsyncSession, worker_id: str, limit: int = 50) -> Sequence[WorkerHeartbeat]:
    stmt = select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == worker_id).order_by(WorkerHeartbeat.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def register_worker(db: AsyncSession, worker: Worker) -> Worker:
    db.add(worker)
    await db.flush()
    await db.refresh(worker)
    return worker

async def update_worker(db: AsyncSession, worker: Worker) -> Worker:
    await db.flush()
    await db.refresh(worker)
    return worker
