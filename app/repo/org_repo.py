from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.organization import Organization
from app.models.org_member import OrgMember

async def get_org_by_slug(db: AsyncSession, slug: str) -> Organization | None:
    stmt = select(Organization).where(Organization.slug == slug)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_organization(db: AsyncSession, org: Organization) -> Organization:
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org

async def add_member(db: AsyncSession, member: OrgMember) -> OrgMember:
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member

async def get_user_organizations(db: AsyncSession, user_id: str) -> list[Organization]:
    stmt = (
        select(Organization)
        .join(OrgMember, OrgMember.org_id == Organization.id)
        .where(OrgMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
