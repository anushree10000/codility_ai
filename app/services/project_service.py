from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.project import OrganizationCreate, ProjectCreate
from app.models.organization import Organization
from app.models.org_member import OrgMember
from app.models.project import Project
from app.repositories import org_repo, project_repo
from app.core.exceptions import ConflictException, NotFoundException
import uuid
from datetime import datetime, timezone

async def create_organization(db: AsyncSession, data: OrganizationCreate, user_id: str) -> Organization:
    existing = await org_repo.get_org_by_slug(db, data.slug)
    if existing:
        raise ConflictException("Organization slug already exists")

    org = Organization(
        id=str(uuid.uuid4()),
        name=data.name,
        slug=data.slug,
        created_at=datetime.now(timezone.utc)
    )
    org = await org_repo.create_organization(db, org)
    
    member = OrgMember(
        id=str(uuid.uuid4()),
        user_id=user_id,
        org_id=org.id,
        role="owner",
        joined_at=datetime.now(timezone.utc)
    )
    await org_repo.add_member(db, member)
    return org

async def create_project(db: AsyncSession, org_id: str, data: ProjectCreate) -> Project:
    existing = await project_repo.get_project_by_slug(db, org_id, data.slug)
    if existing:
        raise ConflictException("Project slug already exists in this organization")

    project = Project(
        id=str(uuid.uuid4()),
        org_id=org_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    return await project_repo.create_project(db, project)

async def check_user_org_access(db: AsyncSession, org_id: str, user_id: str) -> bool:
    # Just a simple check if the user is in the org for now
    orgs = await org_repo.get_user_organizations(db, user_id)
    return any(org.id == org_id for org in orgs)

async def get_project_or_404(db: AsyncSession, project_id: str) -> Project:
    project = await project_repo.get_project_by_id(db, project_id)
    if not project:
        raise NotFoundException("Project not found")
    return project
