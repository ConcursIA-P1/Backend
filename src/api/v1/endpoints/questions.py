from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from src.config.database import get_db
from src.services.question_service import QuestionService
from src.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionFilter,
    QuestionResponse,
    QuestionListResponse,
    QuestionStatsResponse,
    MateriaEnum,
)

router = APIRouter()


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    """Dependency para injetar o serviço de questões."""
    return QuestionService(db)


# ============== ENDPOINTS AUXILIARES (devem vir antes das rotas com parâmetros) ==============

@router.get("/random", response_model=list[QuestionResponse])
def get_random_questions(
    quantidade: int = Query(10, ge=1, le=50, description="Quantidade de questões"),
    ano: Optional[int] = Query(None, ge=1990, le=2030, description="Filtrar por ano"),
    materia: Optional[MateriaEnum] = Query(None, description="Filtrar por matéria"),
    topico: Optional[str] = Query(None, max_length=100, description="Filtrar por tópico"),
    service: QuestionService = Depends(get_question_service)
):
    """
    Retorna N questões aleatórias.
    
    Útil para gerar simulados ou praticar.
    """
    filters = QuestionFilter(ano=ano, materia=materia, topico=topico)
    questions = service.get_random(quantidade, filters)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.get("/stats", response_model=QuestionStatsResponse)
def get_stats(
    service: QuestionService = Depends(get_question_service)
):
    """
    Retorna estatísticas do banco de questões.
    
    Inclui total de questões e contagem por matéria, ano e dificuldade.
    """
    return service.get_stats()


@router.get("/materias", response_model=list[str])
def get_materias(
    service: QuestionService = Depends(get_question_service)
):
    """
    Lista todas as matérias que possuem questões cadastradas.
    """
    return service.get_materias()


@router.get("/topicos", response_model=list[str])
def get_topicos(
    materia: Optional[str] = Query(None, description="Filtrar tópicos por matéria"),
    service: QuestionService = Depends(get_question_service)
):
    """
    Lista todos os tópicos disponíveis.
    
    Opcionalmente filtra por matéria.
    """
    return service.get_topicos(materia)


# ============== LISTAGEM COM FILTROS ==============

@router.get("/", response_model=QuestionListResponse)
def list_questions(
    page: int = Query(1, ge=1, description="Página atual"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    ano: Optional[int] = Query(None, ge=1990, le=2030, description="Filtrar por ano"),
    materia: Optional[MateriaEnum] = Query(None, description="Filtrar por matéria"),
    topico: Optional[str] = Query(None, max_length=100, description="Filtrar por tópico"),
    service: QuestionService = Depends(get_question_service)
):
    """
    Lista questões com filtros e paginação.
    
    Filtros disponíveis:
    - **ano**: Ano da prova (ex: 2023)
    - **materia**: Área do conhecimento (linguagens, humanas, natureza, matematica)
    - **topico**: Tópico específico (busca parcial)
    """
    filters = QuestionFilter(ano=ano, materia=materia, topico=topico)
    return service.list_questions(filters, page, page_size)


# ============== CRUD ENDPOINTS ==============

@router.post("/", response_model=QuestionResponse, status_code=201)
def create_question(
    question_data: QuestionCreate,
    service: QuestionService = Depends(get_question_service)
):
    """
    Cria uma nova questão.
    
    Campos obrigatórios: enunciado, alternativas, gabarito, ano
    """
    question = service.create(question_data)
    return QuestionResponse.model_validate(question)


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    """
    Retorna uma questão pelo ID.
    """
    question = service.get_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return QuestionResponse.model_validate(question)


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: UUID,
    question_data: QuestionUpdate,
    service: QuestionService = Depends(get_question_service)
):
    """
    Atualiza uma questão existente.
    
    Apenas os campos fornecidos serão atualizados.
    """
    question = service.update(question_id, question_data)
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return QuestionResponse.model_validate(question)


@router.delete("/{question_id}", status_code=204)
def delete_question(
    question_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    """
    Remove uma questão pelo ID.
    """
    deleted = service.delete(question_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return None
