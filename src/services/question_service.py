from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import math

from src.models.question import Question
from src.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionFilter,
    QuestionResponse,
    QuestionListResponse,
    QuestionStatsResponse,
)
from src.repositories.question_repository import QuestionRepository


class QuestionService:
    """Serviço para operações de negócio com questões."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = QuestionRepository(db)
    
    # ============== CRUD ==============
    
    def create(self, question_data: QuestionCreate) -> Question:
        """Cria uma nova questão."""
        return self.repository.create(question_data)
    
    def get_by_id(self, question_id: UUID) -> Optional[Question]:
        """Busca questão por ID."""
        return self.repository.get_by_id(question_id)
    
    def update(self, question_id: UUID, question_data: QuestionUpdate) -> Optional[Question]:
        """Atualiza uma questão existente."""
        return self.repository.update(question_id, question_data)
    
    def delete(self, question_id: UUID) -> bool:
        """Remove uma questão."""
        return self.repository.delete(question_id)
    
    # ============== LISTAGEM ==============
    
    def list_questions(
        self,
        filters: Optional[QuestionFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> QuestionListResponse:
        """Lista questões com filtros e paginação."""
        # Limitar page_size
        page_size = min(page_size, 100)
        
        questions, total = self.repository.get_all(filters, page, page_size)
        
        # Calcular total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 0
        
        return QuestionListResponse(
            items=[QuestionResponse.model_validate(q) for q in questions],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    def get_random(
        self,
        quantidade: int = 10,
        filters: Optional[QuestionFilter] = None
    ) -> list[Question]:
        """Busca questões aleatórias."""
        # Limitar quantidade
        quantidade = min(quantidade, 50)
        return self.repository.get_random(quantidade, filters)
    
    # ============== ESTATÍSTICAS ==============
    
    def get_stats(self) -> QuestionStatsResponse:
        """Retorna estatísticas do banco de questões."""
        stats = self.repository.get_stats()
        return QuestionStatsResponse(**stats)
    
    def get_materias(self) -> list[str]:
        """Lista matérias disponíveis."""
        return self.repository.get_materias()
    
    def get_topicos(self, materia: Optional[str] = None) -> list[str]:
        """Lista tópicos disponíveis."""
        return self.repository.get_topicos(materia)
