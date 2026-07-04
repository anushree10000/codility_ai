from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: uuid.UUID | str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
