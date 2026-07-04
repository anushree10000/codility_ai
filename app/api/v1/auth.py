from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, TokenRefresh
from app.services import auth_service
from app.models.user import User
from app.dependencies import get_current_user
from app.core.security import create_access_token, decode_token
from app.core.exceptions import UnauthorizedException

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    return await auth_service.register_user(db, data)

@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access/refresh tokens."""
    return await auth_service.authenticate_user(db, data)

@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh):
    """Refresh an access token using a refresh token."""
    try:
        payload = decode_token(data.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token")
    except Exception:
        raise UnauthorizedException("Invalid refresh token")
        
    new_access = create_access_token(data={"sub": user_id})
    return Token(access_token=new_access, refresh_token=data.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current logged in user."""
    return current_user
