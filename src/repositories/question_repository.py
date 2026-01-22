from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from uuid import UUID
import math

from src.models.question import Question, Materia, Dificuldade
from src.schemas.question import QuestionCreate, QuestionUpdate, QuestionFilter


class QuestionRepository:
    """Repository para operações de banco de dados com questões."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============== CREATE ==============
    
    def create(self, question_data: QuestionCreate) -> Question:
        """Cria uma nova questão no banco."""
        # Converter alternativas para dict
        alternativas_dict = [alt.model_dump() for alt in question_data.alternativas]
        
        db_question = Question(
            enunciado=question_data.enunciado,
            alternativas=alternativas_dict,
            gabarito=question_data.gabarito,
            ano=question_data.ano,
            materia=question_data.materia,
            topico=question_data.topico,
            subtopico=question_data.subtopico,
            dificuldade=question_data.dificuldade,
            banca=question_data.banca,
            prova=question_data.prova,
            numero_questao=question_data.numero_questao,
            explicacao=question_data.explicacao,
            imagem_url=question_data.imagem_url,
            tags=question_data.tags,
        )
        
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question
    
    # ============== READ ==============
    
    def get_by_id(self, question_id: UUID) -> Optional[Question]:
        """Busca questão por ID."""
        return self.db.query(Question).filter(Question.id == question_id).first()
    
    def get_all(
        self,
        filters: Optional[QuestionFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Question], int]:
        """
        Lista questões com filtros e paginação.
        Retorna tuple (lista_questoes, total).
        """
        query = self.db.query(Question)
        
        # Aplicar filtros
        if filters:
            query = self._apply_filters(query, filters)
        
        # Contar total antes de paginar
        total = query.count()
        
        # Ordenar e paginar
        offset = (page - 1) * page_size
        questions = query.order_by(Question.created_at.desc()).offset(offset).limit(page_size).all()
        
        return questions, total
    
    def get_random(
        self,
        quantidade: int = 10,
        filters: Optional[QuestionFilter] = None
    ) -> list[Question]:
        """Busca N questões aleatórias com filtros opcionais."""
        query = self.db.query(Question)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        return query.order_by(func.random()).limit(quantidade).all()
    
    def _apply_filters(self, query, filters: QuestionFilter):
        """Aplica filtros à query."""
        # Filtro por ano
        if filters.ano:
            query = query.filter(Question.ano == filters.ano)
        
        # Filtro por matéria
        if filters.materia:
            query = query.filter(Question.materia == filters.materia)
        
        # Filtro por tópico (busca parcial)
        if filters.topico:
            query = query.filter(Question.topico.ilike(f"%{filters.topico}%"))
        
        return query
    
    # ============== UPDATE ==============
    
    def update(self, question_id: UUID, question_data: QuestionUpdate) -> Optional[Question]:
        """Atualiza uma questão existente."""
        db_question = self.get_by_id(question_id)
        
        if not db_question:
            return None
        
        # Atualizar apenas campos fornecidos
        update_data = question_data.model_dump(exclude_unset=True)
        
        # Converter alternativas se fornecidas
        if "alternativas" in update_data and update_data["alternativas"]:
            update_data["alternativas"] = [alt.model_dump() for alt in question_data.alternativas]
        
        for field, value in update_data.items():
            setattr(db_question, field, value)
        
        self.db.commit()
        self.db.refresh(db_question)
        return db_question
    
    # ============== DELETE ==============
    
    def delete(self, question_id: UUID) -> bool:
        """Remove uma questão. Retorna True se removida, False se não encontrada."""
        db_question = self.get_by_id(question_id)
        
        if not db_question:
            return False
        
        self.db.delete(db_question)
        self.db.commit()
        return True
    
    # ============== STATS ==============
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do banco de questões."""
        total = self.db.query(func.count(Question.id)).scalar()
        
        # Por matéria
        por_materia_query = (
            self.db.query(Question.materia, func.count(Question.id))
            .group_by(Question.materia)
            .all()
        )
        por_materia = {str(m.value) if m else "null": c for m, c in por_materia_query}
        
        # Por ano
        por_ano_query = (
            self.db.query(Question.ano, func.count(Question.id))
            .group_by(Question.ano)
            .order_by(Question.ano.desc())
            .all()
        )
        por_ano = {a: c for a, c in por_ano_query if a}
        
        # Por dificuldade
        por_dificuldade_query = (
            self.db.query(Question.dificuldade, func.count(Question.id))
            .group_by(Question.dificuldade)
            .all()
        )
        por_dificuldade = {str(d.value) if d else "null": c for d, c in por_dificuldade_query}
        
        return {
            "total": total or 0,
            "por_materia": por_materia,
            "por_ano": por_ano,
            "por_dificuldade": por_dificuldade,
        }
    
    # ============== AUXILIARES ==============
    
    def get_materias(self) -> list[str]:
        """Lista todas as matérias com questões cadastradas."""
        result = (
            self.db.query(Question.materia)
            .distinct()
            .filter(Question.materia.isnot(None))
            .all()
        )
        return [m.value for m, in result]
    
    def get_topicos(self, materia: Optional[str] = None) -> list[str]:
        """Lista todos os tópicos, opcionalmente filtrados por matéria."""
        query = (
            self.db.query(Question.topico)
            .distinct()
            .filter(Question.topico.isnot(None))
        )
        
        if materia:
            query = query.filter(Question.materia == materia)
        
        return [t for t, in query.all()]
