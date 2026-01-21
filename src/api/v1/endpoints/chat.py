from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def chat_with_rag():
    """
    Envia uma pergunta para o RAG e recebe resposta.
    TODO: Implementar na Fase 3 (integração com submódulo Chatbot)
    """
    return {"message": "Chat RAG - Em desenvolvimento"}
