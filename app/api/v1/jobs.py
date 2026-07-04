from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.job import JobCreate, JobResponse, JobExecutionResponse, JobLogResponse, DLQResponse
from app.services import job_service, project_service
from app.repositories import job_repo, queue_repo
from app.models.user import User
from app.dependencies import get_current_user
from app.core.exceptions import ForbiddenException

router = APIRouter()

@router.post("/queues/{queue_id}/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(queue_id: str, data: JobCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_repo.get_queue_by_id(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return await job_service.create_job(db, queue_id, data, current_user.id)

@router.get("/queues/{queue_id}/jobs", response_model=list[JobResponse])
async def list_jobs(queue_id: str, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_repo.get_queue_by_id(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return await job_repo.get_queue_jobs(db, queue_id, skip, limit)

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = await job_repo.get_job_by_id(db, job_id)
    queue = await queue_repo.get_queue_by_id(db, job.queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this job")
    return job

@router.get("/jobs/{job_id}/executions", response_model=list[JobExecutionResponse])
async def get_job_executions(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_repo.get_job_executions(db, job_id)

@router.get("/jobs/{job_id}/logs", response_model=list[JobLogResponse])
async def get_job_logs(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_repo.get_job_logs(db, job_id)

@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_service.cancel_job(db, job_id)

@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_service.retry_job(db, job_id)

@router.get("/queues/{queue_id}/dlq", response_model=list[DLQResponse])
async def get_dlq(queue_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_repo.get_queue_dlq(db, queue_id)

@router.post("/dlq/{dlq_id}/requeue", response_model=DLQResponse)
async def requeue_dlq(dlq_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await job_service.requeue_dlq_job(db, dlq_id)
