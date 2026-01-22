from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums para validação
class DificuldadeEnum(str, Enum):
    FACIL = "facil"
    MEDIA = "media"
    DIFICIL = "dificil"


class MateriaEnum(str, Enum):
    LINGUAGENS = "linguagens"
    HUMANAS = "humanas"
    NATUREZA = "natureza"
    MATEMATICA = "matematica"


# Schema para alternativas (request - com validação)
class Alternativa(BaseModel):
    letra: str = Field(..., pattern="^[A-E]$", description="Letra da alternativa (A-E)")
    texto: str = Field(..., min_length=1, description="Texto da alternativa")


# Schema para alternativas (response - sem validação estrita)
class AlternativaResponse(BaseModel):
    letra: str
    texto: str


# ============== REQUEST SCHEMAS ==============

class QuestionCreate(BaseModel):
    """Schema para criação de questão."""
    
    # Campos OBRIGATÓRIOS
    enunciado: str = Field(..., min_length=10, description="Texto do enunciado da questão")
    alternativas: list[Alternativa] = Field(..., min_length=2, max_length=5, description="Lista de alternativas")
    gabarito: str = Field(..., pattern="^[A-E]$", description="Letra da resposta correta")
    ano: int = Field(..., ge=1990, le=2030, description="Ano da prova")
    
    # Campos opcionais
    materia: Optional[MateriaEnum] = Field(None, description="Área do conhecimento")
    topico: Optional[str] = Field(None, max_length=100, description="Tópico específico")
    subtopico: Optional[str] = Field(None, max_length=100, description="Subtópico")
    dificuldade: Optional[DificuldadeEnum] = Field(None, description="Nível de dificuldade")
    banca: Optional[str] = Field(None, max_length=50, description="Banca organizadora")
    
    prova: Optional[str] = Field(None, max_length=50, description="Identificador da prova")
    numero_questao: Optional[int] = Field(None, ge=1, description="Número original na prova")
    
    explicacao: Optional[str] = Field(None, description="Resolução ou comentário")
    imagem_url: Optional[str] = Field(None, max_length=255, description="URL de imagem auxiliar")
    tags: Optional[list[str]] = Field(None, description="Tags adicionais")
    
    @field_validator("gabarito")
    @classmethod
    def gabarito_must_be_in_alternativas(cls, v, info):
        """Valida se o gabarito está entre as alternativas fornecidas."""
        if "alternativas" in info.data:
            letras = [alt.letra for alt in info.data["alternativas"]]
            if v not in letras:
                raise ValueError(f"Gabarito '{v}' não está entre as alternativas: {letras}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "enunciado": "Se f(x) = 2x + 3, qual o valor de f(5)?",
                "alternativas": [
                    {"letra": "A", "texto": "10"},
                    {"letra": "B", "texto": "13"},
                    {"letra": "C", "texto": "15"},
                    {"letra": "D", "texto": "8"},
                    {"letra": "E", "texto": "11"}
                ],
                "gabarito": "B",
                "ano": 2023
            }
        }


class QuestionUpdate(BaseModel):
    """Schema para atualização parcial de questão."""
    
    enunciado: Optional[str] = Field(None, min_length=10)
    alternativas: Optional[list[Alternativa]] = Field(None, min_length=2, max_length=5)
    gabarito: Optional[str] = Field(None, pattern="^[A-E]$")
    
    ano: Optional[int] = Field(None, ge=1990, le=2030)
    materia: Optional[MateriaEnum] = None
    topico: Optional[str] = Field(None, max_length=100)
    subtopico: Optional[str] = Field(None, max_length=100)
    dificuldade: Optional[DificuldadeEnum] = None
    banca: Optional[str] = Field(None, max_length=50)
    
    prova: Optional[str] = Field(None, max_length=50)
    numero_questao: Optional[int] = Field(None, ge=1)
    
    explicacao: Optional[str] = None
    imagem_url: Optional[str] = Field(None, max_length=255)
    tags: Optional[list[str]] = None


class QuestionFilter(BaseModel):
    """Schema para filtros de busca."""
    
    ano: Optional[int] = Field(None, description="Filtrar por ano específico")
    materia: Optional[MateriaEnum] = Field(None, description="Filtrar por matéria")
    topico: Optional[str] = Field(None, description="Filtrar por tópico")


# ============== RESPONSE SCHEMAS ==============

class QuestionResponse(BaseModel):
    """Schema de resposta completa de questão."""
    
    # Campos obrigatórios
    id: UUID
    enunciado: str
    alternativas: list[AlternativaResponse]
    gabarito: str
    ano: int
    
    # Campos opcionais
    materia: Optional[MateriaEnum] = None
    topico: Optional[str] = None
    subtopico: Optional[str] = None
    dificuldade: Optional[DificuldadeEnum] = None
    banca: Optional[str] = None
    
    prova: Optional[str] = None
    numero_questao: Optional[int] = None
    
    explicacao: Optional[str] = None
    imagem_url: Optional[str] = None
    tags: Optional[list[str]] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionMinimal(BaseModel):
    """Schema resumido para listagens."""
    
    id: UUID
    enunciado: str = Field(..., description="Primeiros 150 caracteres do enunciado")
    ano: int
    materia: Optional[MateriaEnum] = None
    dificuldade: Optional[DificuldadeEnum] = None
    
    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Schema de resposta paginada."""
    
    items: list[QuestionResponse]
    total: int = Field(..., description="Total de questões encontradas")
    page: int = Field(..., ge=1, description="Página atual")
    page_size: int = Field(..., ge=1, le=100, description="Itens por página")
    pages: int = Field(..., ge=0, description="Total de páginas")


class QuestionStatsResponse(BaseModel):
    """Schema de estatísticas do banco de questões."""
    
    total: int
    por_materia: dict[str, int]
    por_ano: dict[int, int]
    por_dificuldade: dict[str, int]
