from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.config.database import Base


class UserRole(str, enum.Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"


class User(Base):
    """Modelo de usuário com autenticação."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ALUNO, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    simulados = relationship("Simulado", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
