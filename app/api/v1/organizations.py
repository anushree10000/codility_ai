from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.project import OrganizationCreate, OrganizationResponse, ProjectCreate, ProjectResponse
from app.services import project_service
from app.repositories import org_repo, project_repo
from app.models.user import User
from app.dependencies import get_current_user
from app.core.exceptions import ForbiddenException

router = APIRouter()

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_org(data: OrganizationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await project_service.create_organization(db, data, current_user.id)

@router.get("", response_model=list[OrganizationResponse])
async def list_orgs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await org_repo.get_user_organizations(db, current_user.id)

@router.post("/{org_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_proj(org_id: str, data: ProjectCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await project_service.check_user_org_access(db, org_id, current_user.id):
        raise ForbiddenException("You don't have access to this organization")
    return await project_service.create_project(db, org_id, data)

@router.get("/{org_id}/projects", response_model=list[ProjectResponse])
async def list_projs(org_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await project_service.check_user_org_access(db, org_id, current_user.id):
        raise ForbiddenException("You don't have access to this organization")
    return await project_repo.get_org_projects(db, org_id)
