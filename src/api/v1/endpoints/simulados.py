from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from src.config.database import get_db
from src.services.simulado_service import SimuladoService
from src.schemas.simulado import (
    SimuladoCreate,
    SimuladoQuick,
    SimuladoResponse,
    SimuladoListResponse,
    SimuladoGenerateResult,
)

router = APIRouter()


# ============== ENDPOINTS DE GERAÇÃO ==============

@router.post(
    "/generate",
    response_model=SimuladoGenerateResult,
    summary="Gera simulado personalizado",
    description="""
Gera um simulado com configuração detalhada por matéria.

**Características:**
- Cada matéria pode ter quantidade específica de questões
- Múltiplos tópicos por matéria (distribuição aleatória)
- Filtro por anos
- Evita questões duplicadas

**Exemplo de uso:**
```json
{
    "titulo": "Simulado ENEM 2024",
    "anos": [2022, 2023, 2024],
    "materias_config": [
        {"materia": "matematica", "quantidade": 15},
        {"materia": "linguagens", "quantidade": 15, "topicos": ["Interpretação de Texto"]},
        {"materia": "natureza", "quantidade": 10, "topicos": ["Física", "Química"]},
        {"materia": "humanas", "quantidade": 10}
    ]
}
```
    """
)
def generate_simulado(
    data: SimuladoCreate,
    db: Session = Depends(get_db)
):
    """
    Gera um simulado personalizado com base nos filtros fornecidos.
    
    - **titulo**: Nome opcional do simulado
    - **anos**: Lista de anos para filtrar questões
    - **materias_config**: Configuração detalhada por matéria
        - **materia**: Área do conhecimento (linguagens, humanas, natureza, matematica)
        - **quantidade**: Número de questões desta matéria
        - **topicos**: Lista opcional de tópicos (distribuição aleatória entre eles)
    """
    service = SimuladoService(db)
    return service.generate_simulado(data)


@router.post(
    "/quick",
    response_model=SimuladoGenerateResult,
    summary="Gera simulado rápido",
    description="""
Gera um simulado rápido com distribuição automática entre matérias.

As questões são distribuídas **igualmente** entre as matérias selecionadas.
Se não especificar matérias, usa todas as disponíveis.
    """
)
def generate_quick_simulado(
    data: SimuladoQuick,
    db: Session = Depends(get_db)
):
    """
    Gera um simulado rápido com distribuição automática.
    
    - **quantidade_total**: Número total de questões (distribuídas igualmente)
    - **anos**: Lista opcional de anos para filtrar
    - **materias**: Lista opcional de matérias (se vazio, usa todas)
    """
    service = SimuladoService(db)
    return service.generate_quick_simulado(data)


# ============== ENDPOINTS CRUD ==============

@router.get(
    "",
    response_model=SimuladoListResponse,
    summary="Lista simulados"
)
def list_simulados(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todos os simulados com paginação.
    
    Retorna uma lista resumida (sem as questões completas).
    Para ver as questões, use GET /{simulado_id}.
    """
    service = SimuladoService(db)
    return service.list_simulados(page=page, page_size=page_size)


@router.get(
    "/{simulado_id}",
    response_model=SimuladoResponse,
    summary="Busca simulado por ID"
)
def get_simulado(
    simulado_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Recupera um simulado completo com todas as questões.
    
    - **simulado_id**: UUID do simulado
    """
    service = SimuladoService(db)
    simulado = service.get_by_id(simulado_id)
    
    if not simulado:
        raise HTTPException(
            status_code=404,
            detail=f"Simulado com ID {simulado_id} não encontrado"
        )
    
    return simulado


@router.delete(
    "/{simulado_id}",
    summary="Remove simulado"
)
def delete_simulado(
    simulado_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Remove um simulado.
    
    As questões do banco **não são removidas**, apenas a associação com o simulado.
    """
    service = SimuladoService(db)
    deleted = service.delete(simulado_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Simulado com ID {simulado_id} não encontrado"
        )
    
    return {"message": "Simulado removido com sucesso", "id": str(simulado_id)}


# ============== ENDPOINTS AUXILIARES ==============

@router.get(
    "/{simulado_id}/questions",
    response_model=list,
    summary="Lista apenas as questões de um simulado"
)
def get_simulado_questions(
    simulado_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retorna apenas a lista de questões de um simulado (sem os metadados do simulado).
    
    Útil para interfaces que precisam apenas das questões para exibição.
    """
    service = SimuladoService(db)
    simulado = service.get_by_id(simulado_id)
    
    if not simulado:
        raise HTTPException(
            status_code=404,
            detail=f"Simulado com ID {simulado_id} não encontrado"
        )
    
    return simulado.questions


@router.get(
    "/{simulado_id}/stats",
    summary="Estatísticas de um simulado"
)
def get_simulado_stats(
    simulado_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas de um simulado específico.
    
    - Total de questões
    - Distribuição por matéria
    - Distribuição por ano
    - Filtros aplicados na geração
    """
    service = SimuladoService(db)
    simulado = service.get_by_id(simulado_id)
    
    if not simulado:
        raise HTTPException(
            status_code=404,
            detail=f"Simulado com ID {simulado_id} não encontrado"
        )
    
    # Calcular distribuição por ano
    por_ano: dict[int, int] = {}
    for q in simulado.questions:
        ano = q.get("ano") if isinstance(q, dict) else getattr(q, "ano", None)
        if ano:
            por_ano[ano] = por_ano.get(ano, 0) + 1
    
    return {
        "id": simulado.id,
        "titulo": simulado.titulo,
        "total_questoes": simulado.total_questoes,
        "questoes_por_materia": simulado.questoes_por_materia,
        "questoes_por_ano": por_ano,
        "filtros_aplicados": simulado.filtros_aplicados,
        "created_at": simulado.created_at
    }
