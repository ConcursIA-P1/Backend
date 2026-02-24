from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from src.config import settings
from src.api.v1.router import api_router
from src.core.startup import init_db, check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API backend para a plataforma ConcursIA - Assistente de estudos com RAG",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (must be before exception handlers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para todas as exceções não tratadas."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação."""
    logger.info("🚀 Iniciando aplicação ConcursIA...")
    
    try:
        init_db()
        health = check_database_health()
        
        if health["status"] == "healthy":
            logger.info(f"✓ Banco de dados pronto ({len(health['tables'])} tabelas)")
        else:
            logger.warning(f"⚠ Status do banco: {health['status']}")
            if health["error"]:
                logger.warning(f"  Erro: {health['error']}")
    except Exception as e:
        logger.error(f"✗ Erro ao inicializar: {e}")

# Include routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    """Rota raiz da API."""
    return {
        "message": f"Bem-vindo à {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
