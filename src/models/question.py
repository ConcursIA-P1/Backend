import base64
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from src.config.database import Base


class Dificuldade(str, enum.Enum):
    FACIL = "facil"
    MEDIA = "media"
    DIFICIL = "dificil"


class Materia(str, enum.Enum):
    LINGUAGENS = "linguagens"
    HUMANAS = "humanas"
    NATUREZA = "natureza"
    MATEMATICA = "matematica"


class Question(Base):
    """Modelo de questão do banco de questões."""
    
    __tablename__ = "questions"
    
    # Identificador
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Conteúdo da questão (OBRIGATÓRIOS)
    enunciado = Column(Text, nullable=False)
    alternativas = Column(JSONB, nullable=False)  # [{"letra": "A", "texto": "..."}, ...]
    gabarito = Column(String(1), nullable=False)  # A, B, C, D, E
    ano = Column(Integer, nullable=False, index=True)
    
    # Conteúdo adicional (opcionais)
    explicacao = Column(Text, nullable=True)  # Resolução/comentário
    imagem_blob = Column(LargeBinary, nullable=True) # Imagem em formato binário
    imagem_url = Column(String(255), nullable=True)  # URL de imagem auxiliar

    @property
    def imagem_base64(self) -> str | None:
        if self.imagem_blob:
            # Converte bytes para string base64
            encoded = base64.b64encode(self.imagem_blob).decode("utf-8")
            # Retorna no formato Data URI
            return f"data:image/png;base64,{encoded}"
        return None

    # Metadados para filtros (opcionais)
    materia = Column(Enum(Materia), nullable=True, index=True)
    topico = Column(String(100), nullable=True, index=True)
    subtopico = Column(String(100), nullable=True)
    dificuldade = Column(Enum(Dificuldade), nullable=True, index=True)
    banca = Column(String(50), nullable=True, index=True)
    
    # Informações da prova original
    prova = Column(String(50), nullable=True)  # Ex: "ENEM 2023 - Dia 1"
    numero_questao = Column(Integer, nullable=True)  # Número original na prova
    
    # Tags adicionais
    tags = Column(JSONB, nullable=True)  # ["trigonometria", "função"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Question(id={self.id}, materia={self.materia}, ano={self.ano})>"
