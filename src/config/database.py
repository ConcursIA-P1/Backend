from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# Engine do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexão antes de usar
    echo=settings.DEBUG,  # Log SQL queries em modo debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os models
Base = declarative_base()


def get_db():
    """Dependency para injetar sessão do banco nos endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
