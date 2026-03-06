from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

from src.schemas.question import QuestionResponse, MateriaEnum


# ============== REQUEST SCHEMAS ==============

class MateriaConfig(BaseModel):
    """Configuração de uma matéria para o simulado."""
    materia: MateriaEnum = Field(..., description="Área do conhecimento")
    quantidade: int = Field(..., ge=1, le=50, description="Número de questões desta matéria")
    topicos: Optional[list[str]] = Field(
        None, 
        description="Lista de tópicos. Se vários, questões serão distribuídas aleatoriamente"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "materia": "matematica",
                "quantidade": 10,
                "topicos": ["Geometria", "Álgebra"]
            }
        }


class SimuladoCreate(BaseModel):
    """Schema para criação de simulado personalizado."""
    
    titulo: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Título opcional do simulado"
    )
    
    # Filtros gerais
    anos: Optional[list[int]] = Field(
        None,
        description="Lista de anos para filtrar questões (ex: [2022, 2023, 2024])"
    )
    
    # Configuração por matéria - permite definir quantidade individual
    materias_config: list[MateriaConfig] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Configuração de questões por matéria"
    )
    
    @field_validator("anos")
    @classmethod
    def validate_anos(cls, v):
        if v:
            for ano in v:
                if ano < 1990 or ano > 2030:
                    raise ValueError(f"Ano {ano} fora do intervalo válido (1990-2030)")
        return v
    
    @model_validator(mode="after")
    def validate_total_questoes(self):
        """Valida total de questões e evita duplicação de matérias."""
        materias_vistas = set()
        total = 0
        
        for config in self.materias_config:
            if config.materia in materias_vistas:
                raise ValueError(f"Matéria '{config.materia.value}' duplicada na configuração")
            materias_vistas.add(config.materia)
            total += config.quantidade
        
        if total > 200:
            raise ValueError(f"Total de questões ({total}) excede o limite de 200")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Simulado ENEM 2024",
                "anos": [2022, 2023, 2024],
                "materias_config": [
                    {"materia": "matematica", "quantidade": 15},
                    {"materia": "linguagens", "quantidade": 15, "topicos": ["Interpretação de Texto"]},
                    {"materia": "natureza", "quantidade": 10, "topicos": ["Física", "Química"]},
                    {"materia": "humanas", "quantidade": 10}
                ]
            }
        }


class SimuladoQuick(BaseModel):
    """Schema para geração rápida de simulado (sem configuração detalhada)."""
    
    quantidade_total: int = Field(
        default=45,
        ge=5,
        le=180,
        description="Número total de questões (distribuídas igualmente entre matérias)"
    )
    anos: Optional[list[int]] = Field(
        None,
        description="Lista de anos para filtrar"
    )
    materias: Optional[list[MateriaEnum]] = Field(
        None,
        description="Matérias a incluir. Se vazio, usa todas."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "quantidade_total": 45,
                "anos": [2023, 2024],
                "materias": ["matematica", "linguagens"]
            }
        }


class SimuladoSubmitRequest(BaseModel):
    """Payload para registrar entrega de um simulado."""

    answers: dict[str, str] = Field(
        default_factory=dict,
        description="Mapa de respostas no formato {question_id: alternativa}",
    )


# ============== RESPONSE SCHEMAS ==============

class SimuladoResultado(BaseModel):
    """Resultado consolidado de uma tentativa de simulado."""

    score: int
    total_questoes: int
    answered_count: int
    unanswered_count: int
    percentual: int
    submitted_at: datetime


class SimuladoResponse(BaseModel):
    """Response completa de um simulado."""
    
    id: UUID
    titulo: Optional[str] = None
    filtros_aplicados: Optional[dict] = None
    
    # Questões incluídas
    questions: list[QuestionResponse]
    
    # Estatísticas
    total_questoes: int
    questoes_por_materia: dict[str, int]
    resultado: Optional[SimuladoResultado] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class SimuladoMinimal(BaseModel):
    """Response resumida para listagens."""
    
    id: UUID
    titulo: Optional[str] = None
    total_questoes: int
    resultado: Optional[SimuladoResultado] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SimuladoListResponse(BaseModel):
    """Response paginada de simulados."""
    
    items: list[SimuladoMinimal]
    total: int
    page: int
    page_size: int
    pages: int


class SimuladoGenerateResult(BaseModel):
    """Resultado da geração de simulado com detalhes."""
    
    simulado: SimuladoResponse
    questoes_solicitadas: int
    questoes_encontradas: int
    alertas: list[str] = Field(
        default_factory=list,
        description="Alertas sobre questões não encontradas ou distribuição diferente"
    )


class SimuladoSubmitResponse(BaseModel):
    """Response da entrega de um simulado."""

    simulado_id: UUID
    resultado: SimuladoResultado
