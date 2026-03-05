from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.turma import Turma
from src.models.user import UserRole
from src.repositories.turma_repository import TurmaRepository
from src.repositories.user_repository import UserRepository
from src.schemas.turma import TurmaCreate


class TurmaService:
    """Serviço de regras de negócio para turmas."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TurmaRepository(db)
        self.user_repository = UserRepository(db)

    def create(self, data: TurmaCreate) -> Turma:
        """Cria uma nova turma."""
        professor = None
        if data.professor_id:
            professor = self.user_repository.get_by_id(data.professor_id)
            if not professor:
                raise ValueError(f"Professor com ID {data.professor_id} não encontrado")
            if professor.role != UserRole.PROFESSOR:
                raise ValueError("Usuário informado não é um professor")

        return self.repository.create(nome=data.nome, professor=professor)

    def get_by_id(self, turma_id: UUID) -> Optional[Turma]:
        """Busca turma por ID."""
        return self.repository.get_by_id(turma_id)

    def associar_professor(self, turma_id: UUID, professor_id: UUID) -> Optional[Turma]:
        """Associa um professor a uma turma."""
        turma = self.repository.get_by_id(turma_id)
        if not turma:
            return None

        professor = self.user_repository.get_by_id(professor_id)
        if not professor:
            raise ValueError(f"Professor com ID {professor_id} não encontrado")
        if professor.role != UserRole.PROFESSOR:
            raise ValueError("Usuário informado não é um professor")

        return self.repository.set_professor(turma, professor)

    def adicionar_alunos(self, turma_id: UUID, alunos_ids: List[UUID]) -> Optional[Turma]:
        """Adiciona alunos a uma turma."""
        turma = self.repository.get_by_id(turma_id)
        if not turma:
            return None

        alunos: List = []
        for aluno_id in alunos_ids:
            aluno = self.user_repository.get_by_id(aluno_id)
            if not aluno:
                raise ValueError(f"Aluno com ID {aluno_id} não encontrado")
            if aluno.role != UserRole.ALUNO:
                raise ValueError("Usuário informado não é um aluno")
            alunos.append(aluno)

        return self.repository.add_alunos(turma, alunos)

