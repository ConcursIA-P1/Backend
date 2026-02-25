from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Schema para requisição de chat com RAG."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Pergunta do usuário",
    )

    class Config:
        json_schema_extra = {
            "example": {"message": "Qual a data da prova do ENEM 2024?"}
        }


class ChatResponse(BaseModel):
    """Schema para resposta do chat RAG."""

    answer: str = Field(..., description="Resposta gerada pelo RAG")
    sources: Optional[List[str]] = Field(
        None,
        description="Fontes/documentos utilizados para gerar a resposta",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "A prova do ENEM 2024 será realizada nos dias 3 e 10 de novembro de 2024.",
                "sources": ["edital_enem_2024.pdf"],
            }
        }


class ChatMessageOut(BaseModel):
    """Uma mensagem do histórico."""

    id: str
    role: str
    content: str
    sources: Optional[List[str]] = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Resposta com histórico de mensagens."""

    messages: List[ChatMessageOut]
    total: int
