from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.config.database import Base


# Tabela de associação Many-to-Many entre Simulado e Question
simulado_questions = Table(
    "simulado_questions",
    Base.metadata,
    Column("simulado_id", UUID(as_uuid=True), ForeignKey("simulados.id"), primary_key=True),
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True),
)


class Simulado(Base):
    """Modelo de simulado gerado."""
    
    __tablename__ = "simulados"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    titulo = Column(String(255), nullable=True)
    filtros_aplicados = Column(JSONB, nullable=True)  # Armazena os filtros usados
    
    # Relacionamento com usuário (opcional)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="simulados")
    
    # Relacionamento Many-to-Many com questões
    questions = relationship("Question", secondary=simulado_questions)

    # Relacionamento Many-to-Many com turmas
    turmas = relationship("Turma", secondary="turma_simulados")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Simulado(id={self.id}, titulo={self.titulo})>"
