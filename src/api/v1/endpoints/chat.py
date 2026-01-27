from fastapi import APIRouter, HTTPException, Depends
from functools import lru_cache

from src.schemas.chat import ChatRequest, ChatResponse
from src.services.rag_service import RAGService


router = APIRouter()


@lru_cache()
def get_rag_service() -> RAGService:
    """Dependency para injetar o serviço RAG (singleton)."""
    try:
        return RAGService()
    except ValueError as e:
        # Se API key não estiver configurada, levantar HTTPException
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        # Detectar diferentes tipos de erro e retornar mensagens apropriadas
        if "429" in error_msg or "quota" in error_lower or "exceeded" in error_lower:
            detail = (
                "Quota da API do Google excedida. "
                "Verifique seu plano e limites de uso em: https://ai.google.dev/gemini-api/docs/rate-limits"
            )
            status_code = 429
        elif "dns" in error_lower or "generativelanguage.googleapis.com" in error_lower:
            detail = (
                "A API do Google não está acessível. "
                "Verifique: 1) Conexão com internet 2) Firewall/VPN 3) DNS."
            )
            status_code = 503
        elif "timeout" in error_lower:
            detail = "Timeout ao conectar à API do Google. Verifique sua conexão."
            status_code = 503
        elif "api key" in error_lower or "authentication" in error_lower or "401" in error_msg or "403" in error_msg:
            detail = f"Erro de autenticação: {error_msg}"
            status_code = 401
        else:
            detail = f"Erro ao inicializar serviço RAG: {error_msg}"
            status_code = 503
        
        raise HTTPException(
            status_code=status_code,
            detail=detail
        )


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
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar pergunta: {str(e)}"
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
        info = rag_service.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter informações: {str(e)}"
        )
