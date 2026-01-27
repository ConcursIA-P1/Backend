from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # Aplicação
    APP_NAME: str = "ConcursIA API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Banco de Dados PostgreSQL
    POSTGRES_USER: str = "concursia"
    POSTGRES_PASSWORD: str = "concursia_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "concursia_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # RAG (para integração com o Chatbot)
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"  # Modelo do Gemini a usar
    
    # ChromaDB
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_API_KEY: str = ""
    CHROMA_TENANT: str = ""
    CHROMA_DATABASE: str = ""
    USE_CHROMA_CLOUD: bool = False
    
    # RAG Configuration
    RAG_COLLECTION_NAME: str = "concursia_documents"
    RAG_TOP_K_RESULTS: int = 3  # Número de chunks relevantes para retornar
    EMBEDDING_MODEL: str = "models/embedding-001"  # Modelo de embedding
    COLLECTION_NAME: str = "concursia_documents"  # Nome da collection (alias para RAG_COLLECTION_NAME)
    
    # Configurações adicionais do .env
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    MAX_DOCUMENTS: int = 5
    BATCH_SIZE: int = 50
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
