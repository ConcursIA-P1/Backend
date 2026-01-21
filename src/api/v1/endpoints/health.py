from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.config import get_db, settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Verifica o status da aplicação e conexão com o banco de dados.
    """
    # Testa conexão com o banco
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status
    }
