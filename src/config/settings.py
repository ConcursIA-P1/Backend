from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.
    Todas as variáveis são lidas do .env automaticamente pelo pydantic-settings.
    """

    # Aplicação
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    # Autenticação
    SECRET_KEY: str

    # Banco de Dados PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # RAG e LLM
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    # ChromaDB
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_API_KEY: str = ""
    CHROMA_TENANT: str = ""
    CHROMA_DATABASE: str = ""
    USE_CHROMA_CLOUD: bool = False

    # RAG Configuration
    RAG_COLLECTION_NAME: str = "concursia_documents"
    COLLECTION_NAME: str = "concursia_documents"
    RAG_TOP_K_RESULTS: int = 2
    RAG_MAX_CHUNK_CHARS: int = 500
    RAG_MAX_OUTPUT_TOKENS: int = 512
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
