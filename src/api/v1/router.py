from fastapi import APIRouter
from .endpoints import health, questions, simulados, chat, auth

api_router = APIRouter()

# Autenticação
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticação"]
)

# Health check
api_router.include_router(
    health.router,
    tags=["Health"]
)

# Questões
api_router.include_router(
    questions.router,
    prefix="/questions",
    tags=["Questões"]
)

# Simulados
api_router.include_router(
    simulados.router,
    prefix="/simulados",
    tags=["Simulados"]
)

# Chat RAG
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat RAG"]
)
