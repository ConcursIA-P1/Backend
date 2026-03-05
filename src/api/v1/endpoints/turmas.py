from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.schemas.turma import (
    TurmaCreate,
    TurmaResponse,
    TurmaProfessorRequest,
    TurmaAlunosRequest,
)
from src.schemas.user import UserResponse
from src.services.turma_service import TurmaService


router = APIRouter()


def get_turma_service(db: Session = Depends(get_db)) -> TurmaService:
    """Dependency para injetar o serviço de turmas."""
    return TurmaService(db)


def _to_user_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


def _to_turma_response(turma) -> TurmaResponse:
    professor = _to_user_response(turma.professor) if turma.professor else None
    alunos: List[UserResponse] = [
        _to_user_response(aluno) for aluno in turma.alunos
    ]

    return TurmaResponse(
        id=turma.id,
        nome=turma.nome,
        professor=professor,
        alunos=alunos,
        created_at=turma.created_at,
        updated_at=turma.updated_at,
    )


@router.post(
    "",
    response_model=TurmaResponse,
    summary="Cria uma nova turma",
)
def create_turma(
    data: TurmaCreate,
    service: TurmaService = Depends(get_turma_service),
):
    """Cria uma nova turma."""
    try:
        turma = service.create(data)
        return _to_turma_response(turma)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{turma_id}/professor",
    response_model=TurmaResponse,
    summary="Associa professor a uma turma",
)
def associar_professor(
    turma_id: UUID,
    data: TurmaProfessorRequest,
    service: TurmaService = Depends(get_turma_service),
):
    """Associa um professor a uma turma."""
    turma = service.associar_professor(turma_id, data.professor_id)

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    return _to_turma_response(turma)


@router.post(
    "/{turma_id}/alunos",
    response_model=TurmaResponse,
    summary="Adiciona alunos a uma turma",
)
def adicionar_alunos(
    turma_id: UUID,
    data: TurmaAlunosRequest,
    service: TurmaService = Depends(get_turma_service),
):
    """Adiciona alunos a uma turma."""
    try:
        turma = service.adicionar_alunos(turma_id, data.alunos_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    return _to_turma_response(turma)


@router.get(
    "/{turma_id}/alunos",
    response_model=list[UserResponse],
    summary="Lista alunos de uma turma",
)
def listar_alunos(
    turma_id: UUID,
    service: TurmaService = Depends(get_turma_service),
):
    """Lista alunos de uma turma."""
    turma = service.get_by_id(turma_id)

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    return [_to_user_response(aluno) for aluno in turma.alunos]


@router.get(
    "/{turma_id}/professor",
    response_model=UserResponse,
    summary="Obtém professor de uma turma",
)
def obter_professor(
    turma_id: UUID,
    service: TurmaService = Depends(get_turma_service),
):
    """Obtém o professor de uma turma."""
    turma = service.get_by_id(turma_id)

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    if not turma.professor:
        raise HTTPException(status_code=404, detail="Professor não associado à turma")

    return _to_user_response(turma.professor)

