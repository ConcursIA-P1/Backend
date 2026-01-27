"""
Serviço RAG integrado com o Chatbot (LangGraph).
Usa a arquitetura avançada do submódulo Chatbot.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Adicionar caminho do Chatbot ao sys.path
# Tenta dois caminhos possíveis: relativo ao Backend e absoluto
CHATBOT_PATH_RELATIVE = Path(__file__).parent.parent.parent / "Chatbot" / "src"
CHATBOT_PATH_ABSOLUTE = Path("/Users/andrezavilar/Chatbot/src")

if CHATBOT_PATH_RELATIVE.exists():
    sys.path.insert(0, str(CHATBOT_PATH_RELATIVE))
elif CHATBOT_PATH_ABSOLUTE.exists():
    sys.path.insert(0, str(CHATBOT_PATH_ABSOLUTE))

try:
    from graph import create_enem_rag_graph, ENEMRAGGraph
    from agents import get_retriever
    CHATBOT_AVAILABLE = True
except ImportError as e:
    CHATBOT_AVAILABLE = False
    IMPORT_ERROR = str(e)

from src.config import settings


class ChatbotRAGService:
    """
    Serviço RAG que integra com o submódulo Chatbot.
    Usa LangGraph para processamento avançado com 4 etapas.
    """
    
    def __init__(self):
        """Inicializa o serviço RAG integrado com Chatbot."""
        if not CHATBOT_AVAILABLE:
            raise ImportError(
                f"Não foi possível importar módulos do Chatbot: {IMPORT_ERROR}. "
                "Certifique-se de que o submódulo Chatbot está inicializado."
            )
        
        # Verificar se API key está configurada
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY não configurada. Configure a variável de ambiente GOOGLE_API_KEY."
            )
        
        # Criar grafo RAG usando configurações do .env
        self.rag_graph = create_enem_rag_graph(
            collection_name=settings.COLLECTION_NAME or settings.RAG_COLLECTION_NAME,
            embedding_model=settings.EMBEDDING_MODEL,
            llm_model=settings.GEMINI_MODEL,
            use_cloud=settings.USE_CHROMA_CLOUD,
            chroma_api_key=settings.CHROMA_API_KEY,
            chroma_tenant=settings.CHROMA_TENANT,
            chroma_database=settings.CHROMA_DATABASE,
            max_documents=settings.MAX_DOCUMENTS or settings.RAG_TOP_K_RESULTS,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Obter retriever para informações da collection
        self.retriever = get_retriever()
    
    def query(self, question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa uma pergunta usando o pipeline LangGraph completo.
        
        Args:
            question: Pergunta do usuário
            filters: Filtros opcionais (ex: {"year": 2024, "document_type": "edital"})
            
        Returns:
            dict com 'answer', 'sources', 'is_grounded', etc.
        """
        try:
            # Preparar metadados
            metadata = {
                "filters": filters or {},
                "max_documents": settings.MAX_DOCUMENTS or settings.RAG_TOP_K_RESULTS
            }
            
            # Executar pipeline LangGraph completo
            result = self.rag_graph.invoke(question, metadata)
            
            # Extrair informações
            answer = result.get("final_response", result.get("answer", ""))
            is_grounded = result.get("is_grounded", False)
            documents = result.get("documents", [])
            
            # Extrair fontes
            sources = []
            for doc in documents:
                source = doc.get("source", "N/A")
                if source and source not in sources:
                    sources.append(source)
            
            return {
                "answer": answer,
                "sources": sources if sources else None,
                "is_grounded": is_grounded,
                "documents_count": len(documents)
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Tratamento de erros específicos
            if "quota" in error_msg.lower() or "429" in error_msg:
                return {
                    "answer": "Quota da API do Google excedida. Verifique seu plano e limites de uso.",
                    "sources": None,
                    "is_grounded": False,
                    "documents_count": 0
                }
            
            return {
                "answer": f"Erro ao processar pergunta: {error_msg}",
                "sources": None,
                "is_grounded": False,
                "documents_count": 0
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retorna informações sobre a collection atual."""
        try:
            collection = self.retriever.collection
            count = collection.count()
            
            return {
                "collection_name": self.retriever.collection_name,
                "total_documents": count,
                "embedding_model": settings.EMBEDDING_MODEL,
                "use_chroma_cloud": settings.USE_CHROMA_CLOUD
            }
        except Exception as e:
            return {
                "error": str(e)
            }
