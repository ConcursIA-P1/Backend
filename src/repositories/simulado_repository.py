from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID

from src.models.simulado import Simulado
from src.models.question import Question, Materia


class SimuladoRepository:
    """Repository para operações de banco de dados com simulados."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============== CREATE ==============
    
    def create(
        self, 
        questions: list[Question],
        titulo: Optional[str] = None,
        filtros_aplicados: Optional[dict] = None,
        user_id: Optional[UUID] = None
    ) -> Simulado:
        """Cria um novo simulado com as questões selecionadas."""
        db_simulado = Simulado(
            titulo=titulo,
            filtros_aplicados=filtros_aplicados,
            user_id=user_id,
        )
        
        # Adiciona as questões ao simulado
        db_simulado.questions = questions
        
        self.db.add(db_simulado)
        self.db.commit()
        self.db.refresh(db_simulado)
        return db_simulado
    
    # ============== READ ==============
    
    def get_by_id(self, simulado_id: UUID) -> Optional[Simulado]:
        """Busca simulado por ID."""
        return self.db.query(Simulado).filter(Simulado.id == simulado_id).first()
    
    def get_all(
        self,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Simulado], int]:
        """
        Lista simulados com paginação.
        Se user_id fornecido, filtra por usuário.
        """
        query = self.db.query(Simulado)
        
        if user_id:
            query = query.filter(Simulado.user_id == user_id)
        
        # Contar total
        total = query.count()
        
        # Ordenar e paginar
        offset = (page - 1) * page_size
        simulados = query.order_by(Simulado.created_at.desc()).offset(offset).limit(page_size).all()
        
        return simulados, total
    
    # ============== DELETE ==============
    
    def delete(self, simulado_id: UUID) -> bool:
        """Remove um simulado. Retorna True se removido, False se não encontrado."""
        db_simulado = self.get_by_id(simulado_id)
        
        if not db_simulado:
            return False
        
        self.db.delete(db_simulado)
        self.db.commit()
        return True

    def save_result(self, simulado_id: UUID, resultado: dict) -> Optional[Simulado]:
        """Persiste o resultado mais recente de um simulado em filtros_aplicados."""
        db_simulado = self.get_by_id(simulado_id)

        if not db_simulado:
            return None

        filtros = dict(db_simulado.filtros_aplicados or {})
        filtros["resultado"] = resultado
        db_simulado.filtros_aplicados = filtros

        self.db.add(db_simulado)
        self.db.commit()
        self.db.refresh(db_simulado)
        return db_simulado
    
    # ============== QUESTÕES ==============
    
    def get_random_questions_by_criteria(
        self,
        quantidade: int,
        materia: Optional[Materia] = None,
        topicos: Optional[list[str]] = None,
        anos: Optional[list[int]] = None,
        exclude_ids: Optional[list[UUID]] = None
    ) -> list[Question]:
        """
        Busca questões aleatórias com critérios específicos.
        
        Args:
            quantidade: Número de questões desejado
            materia: Filtro por matéria
            topicos: Lista de tópicos (OR entre eles)
            anos: Lista de anos (OR entre eles)
            exclude_ids: IDs de questões a excluir (evitar duplicatas)
        
        Returns:
            Lista de questões aleatórias
        """
        query = self.db.query(Question)
        
        # Filtro por matéria
        if materia:
            query = query.filter(Question.materia == materia)
        
        # Filtro por anos (OR)
        if anos:
            query = query.filter(Question.ano.in_(anos))
        
        # Filtro por tópicos (OR, busca parcial case-insensitive)
        if topicos:
            from sqlalchemy import or_
            topico_filters = [
                Question.topico.ilike(f"%{topico}%") 
                for topico in topicos
            ]
            query = query.filter(or_(*topico_filters))
        
        # Excluir IDs já selecionados
        if exclude_ids:
            query = query.filter(~Question.id.in_(exclude_ids))
        
        # Retornar questões aleatórias
        return query.order_by(func.random()).limit(quantidade).all()
    
    def count_available_questions(
        self,
        materia: Optional[Materia] = None,
        topicos: Optional[list[str]] = None,
        anos: Optional[list[int]] = None
    ) -> int:
        """Conta questões disponíveis com os critérios fornecidos."""
        query = self.db.query(func.count(Question.id))
        
        if materia:
            query = query.filter(Question.materia == materia)
        
        if anos:
            query = query.filter(Question.ano.in_(anos))
        
        if topicos:
            from sqlalchemy import or_
            topico_filters = [
                Question.topico.ilike(f"%{topico}%") 
                for topico in topicos
            ]
            query = query.filter(or_(*topico_filters))
        
        return query.scalar() or 0
