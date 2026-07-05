from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.queue import QueueCreate, QueueUpdate, QueueResponse, RetryPolicyCreate, RetryPolicyResponse
from app.services import queue_service, project_service
from app.repo import queue_repo
from app.models.user import User
from app.dependencies import get_current_user
from app.core.exceptions import ForbiddenException

router = APIRouter()

@router.post("/projects/{project_id}/queues", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(project_id: str, data: QueueCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = await project_service.get_project_or_404(db, project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this project")
    return await queue_service.create_queue(db, project_id, data)

@router.get("/projects/{project_id}/queues", response_model=list[QueueResponse])
async def list_queues(project_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = await project_service.get_project_or_404(db, project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this project")
    return await queue_repo.get_project_queues(db, project_id)

@router.get("/queues/{queue_id}", response_model=QueueResponse)
async def get_queue(queue_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_service.get_queue_or_404(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return queue

@router.patch("/queues/{queue_id}", response_model=QueueResponse)
async def update_queue(queue_id: str, data: QueueUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_service.get_queue_or_404(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return await queue_service.update_queue(db, queue_id, data)

@router.post("/queues/{queue_id}/pause", response_model=QueueResponse)
async def pause_queue(queue_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_service.get_queue_or_404(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return await queue_service.set_queue_pause_state(db, queue_id, True)

@router.post("/queues/{queue_id}/resume", response_model=QueueResponse)
async def resume_queue(queue_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await queue_service.get_queue_or_404(db, queue_id)
    project = await project_service.get_project_or_404(db, queue.project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this queue")
    return await queue_service.set_queue_pause_state(db, queue_id, False)

@router.post("/retry-policies", response_model=RetryPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_retry_policy(data: RetryPolicyCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await queue_service.create_retry_policy(db, data)

@router.get("/retry-policies", response_model=list[RetryPolicyResponse])
async def list_retry_policies(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await queue_repo.get_retry_policies(db)
