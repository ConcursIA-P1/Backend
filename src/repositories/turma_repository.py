from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.turma import Turma
from src.models.user import User


class TurmaRepository:
    """Repository para operações de banco de dados com turmas."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, turma_id: UUID) -> Optional[Turma]:
        """Busca turma por ID."""
        return self.db.query(Turma).filter(Turma.id == turma_id).first()

    def create(self, nome: str, professor: Optional[User] = None) -> Turma:
        """Cria uma nova turma."""
        turma = Turma(nome=nome, professor=professor)
        self.db.add(turma)
        self.db.commit()
        self.db.refresh(turma)
        return turma

    def set_professor(self, turma: Turma, professor: User) -> Turma:
        """Associa professor à turma."""
        turma.professor = professor
        self.db.commit()
        self.db.refresh(turma)
        return turma

    def add_alunos(self, turma: Turma, alunos: List[User]) -> Turma:
        """Adiciona alunos à turma."""
        existing = {aluno.id for aluno in turma.alunos}
        for aluno in alunos:
            if aluno.id not in existing:
                turma.alunos.append(aluno)
        self.db.commit()
        self.db.refresh(turma)
        return turma

