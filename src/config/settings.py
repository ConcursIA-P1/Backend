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
    
    # RAG (para integração futura com o Chatbot)
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
