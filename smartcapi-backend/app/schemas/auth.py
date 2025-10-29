# smartcapi-backend/app/schemas/auth.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from ..model.tables import UserRole

class UserCreate(BaseModel):
    full_name: Optional[str] = None
    username: str
    password: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[UserRole] = UserRole.ENUMERATOR

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: str
    email: EmailStr
    phone: Optional[str] = None
    voice_sample_path: Optional[str] = None
    role: UserRole

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
