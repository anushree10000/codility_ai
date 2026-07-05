from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.worker import WorkerResponse, WorkerHeartbeatResponse
from app.repo import worker_repo
from app.models.user import User
from app.dependencies import get_current_user
from app.core.exceptions import NotFoundException

router = APIRouter()

@router.get("", response_model=list[WorkerResponse])
async def list_workers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await worker_repo.get_all_workers(db)

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = await worker_repo.get_worker_by_id(db, worker_id)
    if not worker:
        raise NotFoundException("Worker not found")
    return worker

@router.get("/{worker_id}/heartbeats", response_model=list[WorkerHeartbeatResponse])
async def get_worker_heartbeats(worker_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await worker_repo.get_worker_heartbeats(db, worker_id)
