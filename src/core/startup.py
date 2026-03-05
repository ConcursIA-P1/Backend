"""
Funções de inicialização da aplicação.
"""

import logging
from sqlalchemy import inspect, text
from src.config.database import engine

logger = logging.getLogger(__name__)


def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias.
    """
    try:
        # Verificar se conseguimos conectar ao banco
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✓ Conexão com banco de dados estabelecida")
    except Exception as e:
        logger.error(f"✗ Erro ao conectar com banco de dados: {e}")
        raise
    
    # Criar tabelas
    try:
        from src.models.user import User  # noqa: F401
        from src.models.question import Question  # noqa: F401
        from src.models.simulado import Simulado  # noqa: F401
        from src.models.chat_message import ChatMessage  # noqa: F401
        from src.models.turma import Turma  # noqa: F401
        from src.config.database import Base

        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tabelas do banco de dados inicializadas")
        
    except Exception as e:
        logger.error(f"✗ Erro ao inicializar tabelas: {e}")
        raise


def check_database_health():
    """Verifica saúde do banco de dados."""
    result = {
        "status": "unknown",
        "connected": False,
        "tables": [],
        "error": None
    }
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            result["connected"] = True
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            result["tables"] = tables
            
            result["status"] = "healthy" if tables else "warning"
                
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)
    
    return result
