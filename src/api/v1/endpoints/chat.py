from fastapi import APIRouter, HTTPException, Depends
from functools import lru_cache

from src.schemas.chat import ChatRequest, ChatResponse
from src.services.rag_service import RAGService
from src.config import settings


router = APIRouter()
_RAG_INIT_ERROR: str | None = None

class LocalChatFallback:
    """Fallback simples para quando o RAG não está configurado."""

    def query(self, message: str):
        text = message.lower().strip()
        if "enem" in text and "data" in text:
            return {
                "answer": "Ainda não tenho acesso às datas oficiais. Confira o site oficial do INEP para datas atualizadas.",
                "sources": None
            }
        if "matéria" in text or "materia" in text:
            return {
                "answer": "As áreas do ENEM são: Linguagens, Matemática, Ciências Humanas e Ciências da Natureza.",
                "sources": None
            }
        return {
            "answer": (
                "Assistente offline: o serviço de IA não está configurado no servidor. "
                "Configure a variável GOOGLE_API_KEY para respostas avançadas."
            ),
            "sources": None
        }


@lru_cache()
def get_rag_service():
    """Dependency para injetar o serviço RAG (singleton)."""
    global _RAG_INIT_ERROR
    try:
        return RAGService()
    except ValueError as e:
        # Se API key não estiver configurada, usar fallback local
        _RAG_INIT_ERROR = f"RAG init error: {str(e)}"
        return LocalChatFallback()
    except Exception as e:
        # Qualquer outro erro: usar fallback local
        _RAG_INIT_ERROR = f"RAG init error: {str(e)}"
        return LocalChatFallback()


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Chat com RAG",
    description="""
Envia uma pergunta para o sistema RAG e recebe uma resposta baseada nos documentos indexados.

**Como funciona:**
1. A pergunta é convertida em embedding
2. O sistema busca os documentos mais relevantes no ChromaDB
3. O contexto encontrado é usado junto com a pergunta para gerar a resposta via Google Gemini
4. A resposta inclui as fontes utilizadas (quando disponível)

**Nota:** Se nenhum documento foi indexado ainda, o sistema informará que é necessário adicionar documentos primeiro.
    """
)
def chat_with_rag(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Processa uma pergunta usando RAG e retorna a resposta.
    
    - **message**: Pergunta do usuário (máximo 1000 caracteres)
    """
    try:
        result = rag_service.query(request.message)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources")
        )
    except Exception as e:
        # Em caso de erro, responder com fallback amigável ao invés de erro 500
        fallback = LocalChatFallback().query(request.message)
        return ChatResponse(
            answer=fallback["answer"],
            sources=fallback.get("sources")
        )


@router.get(
    "/info",
    summary="Informações do RAG",
    description="Retorna informações sobre a collection de documentos indexados."
)
def get_rag_info(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Retorna informações sobre o estado atual do sistema RAG.
    
    Inclui:
    - Nome da collection
    - Total de documentos indexados
    - Caminho do ChromaDB
    """
    try:
        if hasattr(rag_service, "get_collection_info"):
            info = rag_service.get_collection_info()
            info.update({
                "rag_mode": "google",
                "google_api_key_set": bool(settings.GOOGLE_API_KEY)
            })
            return info
        return {
            "rag_mode": "fallback",
            "google_api_key_set": bool(settings.GOOGLE_API_KEY),
            "message": "Serviço RAG indisponível, usando fallback local.",
            "error": _RAG_INIT_ERROR
        }
    except Exception as e:
        return {
            "rag_mode": "error",
            "google_api_key_set": bool(settings.GOOGLE_API_KEY),
            "detail": f"Erro ao obter informações: {str(e)}"
        }
