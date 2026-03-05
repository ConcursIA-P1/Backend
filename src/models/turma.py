from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.config.database import Base


turma_alunos = Table(
    "turma_alunos",
    Base.metadata,
    Column("turma_id", UUID(as_uuid=True), ForeignKey("turmas.id", ondelete="CASCADE"), primary_key=True),
    Column("aluno_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

turma_simulados = Table(
    "turma_simulados",
    Base.metadata,
    Column("turma_id", UUID(as_uuid=True), ForeignKey("turmas.id", ondelete="CASCADE"), primary_key=True),
    Column("simulado_id", UUID(as_uuid=True), ForeignKey("simulados.id", ondelete="CASCADE"), primary_key=True),
)


class Turma(Base):
    """Modelo de turma."""

    __tablename__ = "turmas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nome = Column(String(255), nullable=False)

    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    professor = relationship("User", foreign_keys=[professor_id])
    alunos = relationship("User", secondary=turma_alunos)
    simulados = relationship("Simulado", secondary=turma_simulados)

    def __repr__(self):
        return f"<Turma(id={self.id}, nome={self.nome})>"
