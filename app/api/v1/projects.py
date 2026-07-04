from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.project import ProjectResponse
from app.services import project_service
from app.models.user import User
from app.dependencies import get_current_user
from app.core.exceptions import ForbiddenException

router = APIRouter()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = await project_service.get_project_or_404(db, project_id)
    if not await project_service.check_user_org_access(db, project.org_id, current_user.id):
        raise ForbiddenException("You don't have access to this project")
    return project
