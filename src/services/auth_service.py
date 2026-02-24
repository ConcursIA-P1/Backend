"""
Serviço de autenticação com JWT e hash de senha.
"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserLogin, UserResponse, UserRole


class AuthService:
    """Serviço de autenticação."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
        self.secret_key = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key"
        self.algorithm = "HS256"
        self.token_expiration = 24  # horas

    @staticmethod
    def hash_password(password: str) -> str:
        """Cria hash da senha."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica se a senha corresponde ao hash."""
        return AuthService.hash_password(password) == password_hash

    def register(self, data: UserCreate) -> UserResponse:
        """Registra novo usuário."""
        # Verificar se email já existe
        if self.repository.email_exists(data.email):
            raise ValueError(f"Email {data.email} já está registrado")

        # Hash da senha
        password_hash = self.hash_password(data.password)

        # Criar usuário
        user = self.repository.create(
            email=data.email,
            name=data.name,
            password_hash=password_hash,
            role=data.role
        )

        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value if isinstance(user.role, UserRole) else user.role,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )

    def login(self, data: UserLogin) -> dict:
        """Autentica usuário e retorna token."""
        # Buscar usuário
        user = self.repository.get_by_email(data.email)
        
        if not user:
            raise ValueError("Email ou senha incorretos")

        # Verificar senha
        if not self.verify_password(data.password, user.password_hash):
            raise ValueError("Email ou senha incorretos")

        # Criar JWT
        token = self.create_token(str(user.id))

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role.value if isinstance(user.role, UserRole) else user.role,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat()
            )
        }

    def create_token(self, user_id: str) -> str:
        """Cria JWT token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiration),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verifica e retorna user_id do token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("user_id")
            if user_id is None:
                return None
            return user_id
        except jwt.InvalidTokenError:
            return None
