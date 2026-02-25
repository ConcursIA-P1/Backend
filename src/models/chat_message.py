from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.config.database import Base


class ChatMessage(Base):
    """Mensagem de chat persistida no banco."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" ou "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Lista de fontes (apenas para assistant)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, user_id={self.user_id}, role={self.role})>"
