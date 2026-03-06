from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.user import UserResponse


class TurmaBase(BaseModel):
    """Base de turma."""

    nome: str = Field(..., max_length=255, description="Nome da turma")


class TurmaCreate(TurmaBase):
    """Schema para criação de turma."""

    professor_id: Optional[UUID] = Field(
        None,
        description="ID do professor responsável pela turma",
    )


class TurmaResponse(BaseModel):
    """Schema de resposta de turma com professor e alunos."""

    id: UUID
    nome: str
    professor: Optional[UserResponse] = None
    alunos: List[UserResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TurmaProfessorRequest(BaseModel):
    """Request para associação de professor a turma."""

    professor_id: UUID = Field(..., description="ID do professor a ser associado")


class TurmaAlunosRequest(BaseModel):
    """Request para associação de alunos a turma."""

    alunos_ids: List[UUID] = Field(
        ...,
        min_length=1,
        description="Lista de IDs de alunos a serem associados à turma",
    )

