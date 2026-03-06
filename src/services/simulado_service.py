from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import math
from datetime import datetime, timezone

from src.repositories.simulado_repository import SimuladoRepository
from src.models.simulado import Simulado
from src.models.question import Question, Materia
from src.schemas.simulado import (
    SimuladoCreate,
    SimuladoQuick,
    SimuladoResponse,
    SimuladoMinimal,
    SimuladoListResponse,
    SimuladoGenerateResult,
    SimuladoResultado,
    SimuladoSubmitResponse,
    MateriaConfig,
)
from src.schemas.question import MateriaEnum


class SimuladoService:
    """Serviço de lógica de negócio para simulados."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = SimuladoRepository(db)
    
    def generate_simulado(
        self,
        data: SimuladoCreate,
        user_id: Optional[UUID] = None
    ) -> SimuladoGenerateResult:
        """
        Gera um simulado personalizado com configuração detalhada por matéria.
        
        Cada matéria pode ter:
        - Quantidade específica de questões
        - Lista de tópicos (distribuição aleatória entre eles)
        """
        all_questions: list[Question] = []
        alertas: list[str] = []
        total_solicitado = 0
        questoes_por_materia: dict[str, int] = {}
        
        # Coletar IDs já usados para evitar duplicatas
        used_ids: list[UUID] = []
        
        # Processar cada configuração de matéria
        for config in data.materias_config:
            total_solicitado += config.quantidade
            
            # Converter MateriaEnum para Materia do modelo
            materia_model = Materia(config.materia.value)
            
            # Buscar questões para esta matéria
            questions = self.repository.get_random_questions_by_criteria(
                quantidade=config.quantidade,
                materia=materia_model,
                topicos=config.topicos,
                anos=data.anos,
                exclude_ids=used_ids if used_ids else None
            )
            
            # Registrar questões encontradas
            found_count = len(questions)
            questoes_por_materia[config.materia.value] = found_count
            
            # Adicionar alerta se não encontrou todas
            if found_count < config.quantidade:
                disponivel = self.repository.count_available_questions(
                    materia=materia_model,
                    topicos=config.topicos,
                    anos=data.anos
                )
                alertas.append(
                    f"Matéria '{config.materia.value}': solicitado {config.quantidade}, "
                    f"encontrado {found_count} (disponível: {disponivel})"
                )
            
            # Adicionar aos resultados
            all_questions.extend(questions)
            used_ids.extend([q.id for q in questions])
        
        # Criar o simulado no banco
        filtros_aplicados = {
            "anos": data.anos,
            "materias_config": [
                {
                    "materia": c.materia.value,
                    "quantidade": c.quantidade,
                    "topicos": c.topicos
                }
                for c in data.materias_config
            ]
        }
        
        simulado = self.repository.create(
            questions=all_questions,
            titulo=data.titulo,
            filtros_aplicados=filtros_aplicados,
            user_id=user_id
        )
        
        # Construir response
        return SimuladoGenerateResult(
            simulado=self._to_response(simulado, questoes_por_materia),
            questoes_solicitadas=total_solicitado,
            questoes_encontradas=len(all_questions),
            alertas=alertas
        )
    
    def generate_quick_simulado(
        self,
        data: SimuladoQuick,
        user_id: Optional[UUID] = None
    ) -> SimuladoGenerateResult:
        """
        Gera um simulado rápido com distribuição automática.
        
        As questões são distribuídas igualmente entre as matérias selecionadas.
        """
        # Determinar matérias a usar
        materias = data.materias or list(MateriaEnum)
        num_materias = len(materias)
        
        # Calcular quantidade por matéria
        base_quantidade = data.quantidade_total // num_materias
        resto = data.quantidade_total % num_materias
        
        # Criar configuração por matéria
        materias_config = []
        for i, materia in enumerate(materias):
            # Distribuir o resto nas primeiras matérias
            qtd = base_quantidade + (1 if i < resto else 0)
            materias_config.append(MateriaConfig(
                materia=materia,
                quantidade=qtd,
                topicos=None
            ))
        
        # Reutilizar lógica do generate_simulado
        simulado_create = SimuladoCreate(
            titulo=f"Simulado Rápido - {data.quantidade_total} questões",
            anos=data.anos,
            materias_config=materias_config
        )
        
        return self.generate_simulado(simulado_create, user_id)
    
    def get_by_id(self, simulado_id: UUID) -> Optional[SimuladoResponse]:
        """Busca simulado por ID."""
        simulado = self.repository.get_by_id(simulado_id)
        
        if not simulado:
            return None
        
        # Calcular questões por matéria
        questoes_por_materia = self._count_by_materia(simulado.questions)
        
        return self._to_response(simulado, questoes_por_materia)

    def submit_result(
        self,
        simulado_id: UUID,
        answers: dict[str, str],
    ) -> Optional[SimuladoSubmitResponse]:
        """Registra o resultado de uma tentativa de simulado."""
        simulado = self.repository.get_by_id(simulado_id)
        if not simulado:
            return None

        questions = simulado.questions or []
        total = len(questions)

        normalized_answers: dict[str, str] = {
            str(question_id): value.strip().upper()
            for question_id, value in (answers or {}).items()
            if value
        }

        score = 0
        answered_count = 0
        for q in questions:
            answer = normalized_answers.get(str(q.id))
            if answer:
                answered_count += 1
                if answer == q.gabarito:
                    score += 1

        unanswered_count = max(total - answered_count, 0)
        percentual = round((score / total) * 100) if total > 0 else 0
        submitted_at = datetime.now(timezone.utc)

        resultado = {
            "score": score,
            "total_questoes": total,
            "answered_count": answered_count,
            "unanswered_count": unanswered_count,
            "percentual": percentual,
            "submitted_at": submitted_at.isoformat(),
        }

        updated = self.repository.save_result(simulado_id, resultado)
        if not updated:
            return None

        parsed_result = self._extract_resultado(updated)
        if not parsed_result:
            return None

        return SimuladoSubmitResponse(
            simulado_id=updated.id,
            resultado=parsed_result,
        )
    
    def list_simulados(
        self,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SimuladoListResponse:
        """Lista simulados com paginação."""
        simulados, total = self.repository.get_all(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        pages = math.ceil(total / page_size) if total > 0 else 0
        
        items = [
            SimuladoMinimal(
                id=s.id,
                titulo=s.titulo,
                total_questoes=len(s.questions),
                resultado=self._extract_resultado(s),
                created_at=s.created_at
            )
            for s in simulados
        ]
        
        return SimuladoListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    
    def delete(self, simulado_id: UUID) -> bool:
        """Remove um simulado."""
        return self.repository.delete(simulado_id)
    
    # ============== HELPERS ==============
    
    def _count_by_materia(self, questions: list[Question]) -> dict[str, int]:
        """Conta questões por matéria."""
        count: dict[str, int] = {}
        for q in questions:
            materia_key = q.materia.value if q.materia else "sem_materia"
            count[materia_key] = count.get(materia_key, 0) + 1
        return count
    
    def _to_response(
        self, 
        simulado: Simulado,
        questoes_por_materia: dict[str, int]
    ) -> SimuladoResponse:
        """Converte modelo para response."""
        from src.schemas.question import QuestionResponse
        
        return SimuladoResponse(
            id=simulado.id,
            titulo=simulado.titulo,
            filtros_aplicados=simulado.filtros_aplicados,
            questions=[
                QuestionResponse.model_validate(q) 
                for q in simulado.questions
            ],
            total_questoes=len(simulado.questions),
            questoes_por_materia=questoes_por_materia,
            resultado=self._extract_resultado(simulado),
            created_at=simulado.created_at
        )

    def _extract_resultado(self, simulado: Simulado) -> Optional[SimuladoResultado]:
        """Extrai resultado persistido de filtros_aplicados, quando existir."""
        filtros = simulado.filtros_aplicados or {}
        resultado = filtros.get("resultado") if isinstance(filtros, dict) else None
        if not resultado:
            return None

        try:
            return SimuladoResultado.model_validate(resultado)
        except Exception:
            return None
