from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.project import Project

async def get_project_by_slug(db: AsyncSession, org_id: str, slug: str) -> Project | None:
    stmt = select(Project).where(Project.org_id == org_id, Project.slug == slug)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_project(db: AsyncSession, project: Project) -> Project:
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project

async def get_org_projects(db: AsyncSession, org_id: str) -> list[Project]:
    stmt = select(Project).where(Project.org_id == org_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_project_by_id(db: AsyncSession, project_id: str) -> Project | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
