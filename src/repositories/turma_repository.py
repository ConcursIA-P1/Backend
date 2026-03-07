from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.turma import Turma, _generate_codigo
from src.models.user import User
from src.models.simulado import Simulado


class TurmaRepository:
    """Repository para operações de banco de dados com turmas."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, turma_id: UUID) -> Optional[Turma]:
        """Busca turma por ID."""
        return self.db.query(Turma).filter(Turma.id == turma_id).first()

    def list_by_professor(self, professor_id: UUID) -> list[Turma]:
        """Lista turmas de um professor."""
        return (
            self.db.query(Turma)
            .filter(Turma.professor_id == professor_id)
            .order_by(Turma.created_at.desc())
            .all()
        )

    def list_by_aluno(self, aluno_id: UUID) -> list[Turma]:
        """Lista turmas em que um aluno esta matriculado."""
        return (
            self.db.query(Turma)
            .join(Turma.alunos)
            .filter(User.id == aluno_id)
            .order_by(Turma.created_at.desc())
            .all()
        )

    def create(self, nome: str, professor: Optional[User] = None) -> Turma:
        """Cria uma nova turma."""
        codigo = _generate_codigo()
        turma = Turma(nome=nome, professor=professor, codigo=codigo)
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

    def get_by_codigo(self, codigo: str) -> Optional[Turma]:
        """Busca turma por código."""
        return self.db.query(Turma).filter(Turma.codigo == codigo.upper().strip()).first()

    def add_simulado(self, turma: Turma, simulado: Simulado) -> Turma:
        """Atribui um simulado à turma."""
        if all(s.id != simulado.id for s in turma.simulados):
            turma.simulados.append(simulado)
            self.db.commit()
            self.db.refresh(turma)
        return turma

