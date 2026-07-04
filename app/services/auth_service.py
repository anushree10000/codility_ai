from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User
from app.repositories import user_repo
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import ConflictException, UnauthorizedException
import uuid
from datetime import datetime, timezone

async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing_user = await user_repo.get_user_by_email(db, data.email)
    if existing_user:
        raise ConflictException("Email already registered")

    new_user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    return await user_repo.create_user(db, new_user)

async def authenticate_user(db: AsyncSession, data: UserLogin) -> Token:
    user = await user_repo.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password")
    
    if not user.is_active:
        raise UnauthorizedException("User is inactive")

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return Token(access_token=access_token, refresh_token=refresh_token)
