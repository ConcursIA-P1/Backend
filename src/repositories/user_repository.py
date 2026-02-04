"""
Repository para operações de banco de dados com usuários.
"""

from sqlalchemy.orm import Session
from typing import Optional, Union
from uuid import UUID

from src.models.user import User, UserRole


class UserRepository:
    """Repository para operações com usuários."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuário por ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create(
        self,
        email: str,
        name: str,
        password_hash: str,
        role: Union[str, UserRole] = "aluno"
    ) -> User:
        """Cria novo usuário."""
        # Converter string para Enum se necessário
        if isinstance(role, str):
            role = UserRole(role)
        
        db_user = User(
            email=email,
            name=name,
            password_hash=password_hash,
            role=role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Atualiza usuário."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: UUID) -> bool:
        """Deleta usuário."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def email_exists(self, email: str) -> bool:
        """Verifica se email já existe."""
        return self.db.query(User).filter(User.email == email).first() is not None
