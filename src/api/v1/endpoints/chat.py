from fastapi import APIRouter, Depends, Header
from functools import lru_cache
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from src.schemas.chat import ChatRequest, ChatResponse, ChatMessageOut, ChatHistoryResponse
from src.services.rag_service import RAGService
from src.services.auth_service import AuthService
from src.config import settings
from src.config.database import get_db
from src.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter()
_RAG_INIT_ERROR: str | None = None


class LocalChatFallback:
    """Fallback quando o RAG não está disponível."""

    def query(self, message: str):
        return {
            "answer": (
                f"Assistente offline: não foi possível iniciar o serviço de IA. "
                f"Erro: {_RAG_INIT_ERROR or 'desconhecido'}"
            ),
            "sources": None,
        }


@lru_cache()
def get_rag_service():
    """Dependency para injetar o serviço RAG (singleton)."""
    global _RAG_INIT_ERROR
    try:
        service = RAGService()
        logger.info("✅ RAGService inicializado com sucesso")
        return service
    except Exception as e:
        _RAG_INIT_ERROR = str(e)
        logger.error("❌ RAGService falhou ao inicializar: %s", e, exc_info=True)
        return LocalChatFallback()


def _get_user_id(authorization: Optional[str], db: Session) -> Optional[str]:
    """Extrai user_id do header Authorization (Bearer token). Retorna None se ausente/inválido."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]  # Remove "Bearer "
    service = AuthService(db)
    return service.verify_token(token)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat com RAG",
    description="Envia uma pergunta para o sistema RAG. Se autenticado, salva no histórico.",
)
def chat_with_rag(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db),
):
    """
    Processa uma pergunta usando RAG e retorna a resposta.
    Se o header Authorization estiver presente, salva a mensagem no histórico.
    """
    try:
        result = rag_service.query(request.message)
        answer = result["answer"]
        sources = result.get("sources")

        # Salvar no histórico se o usuário estiver autenticado
        user_id = _get_user_id(authorization, db)
        if user_id:
            try:
                uid = UUID(user_id)
                # Salvar pergunta do usuário
                user_msg = ChatMessage(user_id=uid, role="user", content=request.message)
                db.add(user_msg)
                # Salvar resposta do assistente
                assistant_msg = ChatMessage(
                    user_id=uid, role="assistant", content=answer, sources=sources
                )
                db.add(assistant_msg)
                db.commit()
            except Exception as e:
                logger.warning("Falha ao salvar histórico: %s", e)
                db.rollback()

        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error("Erro no chat RAG: %s", e)
        return ChatResponse(
            answer=f"Ocorreu um erro ao processar sua pergunta: {str(e)}",
            sources=None,
        )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Histórico de chat",
    description="Retorna o histórico de mensagens do usuário autenticado.",
)
def get_chat_history(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Retorna histórico de chat do usuário."""
    user_id = _get_user_id(authorization, db)
    if not user_id:
        return ChatHistoryResponse(messages=[], total=0)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == UUID(user_id))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return ChatHistoryResponse(
        messages=[
            ChatMessageOut(
                id=str(m.id),
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
        total=len(messages),
    )


@router.delete(
    "/history",
    summary="Limpar histórico",
    description="Apaga todo o histórico de chat do usuário autenticado.",
)
def clear_chat_history(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Limpa histórico de chat do usuário."""
    user_id = _get_user_id(authorization, db)
    if not user_id:
        return {"message": "Não autenticado", "deleted": 0}

    count = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == UUID(user_id))
        .delete()
    )
    db.commit()

    return {"message": "Histórico limpo", "deleted": count}


@router.get(
    "/info",
    summary="Informações do RAG",
    description="Retorna informações sobre a collection de documentos indexados.",
)
def get_rag_info(
    rag_service: RAGService = Depends(get_rag_service),
):
    """Retorna informações sobre o estado atual do sistema RAG."""
    try:
        if hasattr(rag_service, "get_collection_info"):
            info = rag_service.get_collection_info()
            info.update({
                "rag_mode": "google",
                "google_api_key_set": bool(settings.GOOGLE_API_KEY),
            })
            return info
        return {
            "rag_mode": "fallback",
            "google_api_key_set": bool(settings.GOOGLE_API_KEY),
            "message": "Serviço RAG indisponível, usando fallback local.",
            "error": _RAG_INIT_ERROR,
        }
    except Exception as e:
        return {
            "rag_mode": "error",
            "google_api_key_set": bool(settings.GOOGLE_API_KEY),
            "detail": f"Erro ao obter informações: {str(e)}",
        }
