"""
Schemas para autenticação e usuários.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuário."""
    ALUNO = "aluno"
    PROFESSOR = "professor"


class UserBase(BaseModel):
    """Base para usuário."""
    email: EmailStr
    name: str
    role: UserRole = UserRole.ALUNO


class UserCreate(UserBase):
    """Schema para criação de usuário."""
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema de resposta de usuário."""
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema de resposta com token."""
    access_token: str
    token_type: str
    user: UserResponse


class AuthResponse(BaseModel):
    """Schema de resposta de autenticação."""
    success: bool
    message: str
    user: Optional[UserResponse] = None
    token: Optional[str] = None
