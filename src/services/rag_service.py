import os
from typing import Optional, List
from pathlib import Path

# Configurar variáveis de ambiente gRPC antes de importar bibliotecas do Google
# Isso ajuda a resolver problemas de DNS/conectividade
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")
# Forçar IPv4 pode ajudar em alguns ambientes
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")  # Reduzir logs verbosos

from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config import settings


class RAGService:
    """Serviço para operações de RAG (Retrieval-Augmented Generation)."""
    
    def __init__(self):
        """Inicializa o serviço RAG com ChromaDB e Google Gemini."""
        # Usar COLLECTION_NAME do .env se disponível, senão RAG_COLLECTION_NAME
        self.collection_name = settings.COLLECTION_NAME or settings.RAG_COLLECTION_NAME
        self.chroma_path = Path(settings.CHROMA_DB_PATH)
        if not settings.USE_CHROMA_CLOUD:
            self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Verificar se API key está configurada
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY não configurada. Configure a variável de ambiente GOOGLE_API_KEY."
            )
        
        # Inicializar embeddings
        # Nota: Se EMBEDDING_MODEL for diferente de models/embedding-001, 
        # pode ser necessário usar outro provider (ex: HuggingFace)
        embedding_model = settings.EMBEDDING_MODEL
        
        # Configurações para tentar resolver problemas de DNS/gRPC
        embedding_kwargs = {
            "google_api_key": settings.GOOGLE_API_KEY,
            "request_timeout": 120,
            # Usar transporte HTTP em vez de gRPC pode ajudar em alguns casos
            # Mas a biblioteca atual não suporta isso diretamente
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if embedding_model.startswith("models/"):
                    # Modelo do Google
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=embedding_model,
                        **embedding_kwargs
                    )
                else:
                    # Para outros modelos (ex: BAAI/bge-m3), usar Google por enquanto
                    # TODO: Adicionar suporte para outros providers de embedding
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/embedding-001",
                        **embedding_kwargs
                    )
                # Se chegou aqui, sucesso!
                break
            except Exception as e:
                error_msg = str(e).lower()
                if attempt < max_retries - 1:
                    # Se for erro de DNS/conectividade, tentar novamente
                    if "dns" in error_msg or "timeout" in error_msg or "503" in error_msg:
                        import time
                        time.sleep(retry_delay * (attempt + 1))  # Backoff exponencial
                        # Aumentar timeout em cada tentativa
                        embedding_kwargs["request_timeout"] = 120 + (attempt * 60)
                        continue
                # Se esgotou tentativas ou erro diferente, relançar
                raise
        
        # Inicializar ChromaDB
        self.vectorstore = self._init_vectorstore()
        
        # Inicializar LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True,
            request_timeout=120  # Aumentar timeout
        )
        
        # Criar chain RAG
        self.retriever = self._create_retriever()
        self.qa_chain = self._create_qa_chain()
    
    def _init_vectorstore(self) -> Chroma:
        """Inicializa ou carrega o ChromaDB vector store."""
        try:
            # Verificar se deve usar ChromaDB Cloud
            if settings.USE_CHROMA_CLOUD:
                import chromadb
                
                # Configurar cliente ChromaDB Cloud
                chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    port=443,
                    ssl=True,
                    headers={
                        "X-Chroma-Token": settings.CHROMA_API_KEY,
                        "X-Chroma-Tenant": settings.CHROMA_TENANT,
                    }
                )
                
                # Criar vectorstore usando cliente Cloud
                vectorstore = Chroma(
                    client=chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
            else:
                # Usar ChromaDB local
                vectorstore = Chroma(
                    persist_directory=str(self.chroma_path),
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
            
            # Verificar se há documentos
            collection = vectorstore._collection
            count = collection.count()
            
            if count == 0:
                # Se não há documentos, criar um documento placeholder
                # Isso evita erros quando o banco está vazio
                vectorstore.add_texts(
                    texts=["Nenhum documento foi indexado ainda. Por favor, adicione documentos primeiro."],
                    ids=["placeholder"]
                )
            
            return vectorstore
        except Exception as e:
            # Se houver erro, criar novo vectorstore
            vectorstore = Chroma(
                persist_directory=str(self.chroma_path),
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
            # Adicionar placeholder
            vectorstore.add_texts(
                texts=["Nenhum documento foi indexado ainda. Por favor, adicione documentos primeiro."],
                ids=["placeholder"]
            )
            return vectorstore
    
    def _create_retriever(self):
        """Cria o retriever para buscar documentos relevantes."""
        return self.vectorstore.as_retriever(
            search_kwargs={"k": settings.RAG_TOP_K_RESULTS}
        )
    
    def _create_qa_chain(self):
        """Cria a chain de Q&A com RAG usando LCEL."""
        # Template de prompt customizado
        prompt_template = """Você é um assistente especializado em concursos públicos e provas como ENEM.

Use APENAS as informações fornecidas no contexto abaixo para responder a pergunta.
Se a informação não estiver no contexto, diga claramente que não possui essa informação.

Contexto:
{context}

Pergunta: {question}

Resposta:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Criar chain usando LCEL (LangChain Expression Language)
        def format_docs(docs):
            """Formata os documentos retornados pelo retriever."""
            return "\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def query(self, question: str) -> dict:
        """
        Processa uma pergunta e retorna resposta com RAG.
        
        Args:
            question: Pergunta do usuário
            
        Returns:
            dict com 'answer' e 'sources'
        """
        try:
            # Buscar documentos relevantes primeiro para obter sources
            docs = self.retriever.invoke(question)
            
            # Executar query na chain
            answer = self.qa_chain.invoke(question)
            
            # Extrair fontes dos documentos retornados
            sources = []
            for doc in docs:
                # Tentar extrair metadata com informações sobre o documento
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                source = metadata.get('source', 'Documento desconhecido')
                if source and source not in sources and source != 'placeholder':
                    sources.append(source)
            
            # Se não há fontes, mas há resposta, pode ser do placeholder
            if not sources and "Nenhum documento foi indexado" in answer:
                return {
                    "answer": "Nenhum documento foi indexado ainda no sistema. Por favor, adicione documentos primeiro para que eu possa responder suas perguntas.",
                    "sources": []
                }
            
            return {
                "answer": answer,
                "sources": sources if sources else None
            }
            
        except Exception as e:
            # Tratar erros de forma amigável
            error_msg = str(e)
            
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return {
                    "answer": "Erro de autenticação com o serviço de IA. Verifique se a GOOGLE_API_KEY está configurada corretamente.",
                    "sources": None
                }
            
            return {
                "answer": f"Ocorreu um erro ao processar sua pergunta: {error_msg}",
                "sources": None
            }
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None, ids: Optional[List[str]] = None):
        """
        Adiciona documentos ao vector store.
        
        Args:
            texts: Lista de textos para indexar
            metadatas: Lista opcional de metadados (ex: [{"source": "edital_2024.pdf"}])
            ids: Lista opcional de IDs únicos para os documentos
        """
        try:
            # Remover placeholder se existir
            collection = self.vectorstore._collection
            try:
                collection.delete(ids=["placeholder"])
            except:
                pass
            
            # Adicionar novos documentos
            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
        except Exception as e:
            raise Exception(f"Erro ao adicionar documentos: {str(e)}")
    
    def get_collection_info(self) -> dict:
        """Retorna informações sobre a collection atual."""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "chroma_path": str(self.chroma_path)
            }
        except Exception as e:
            return {
                "error": str(e)
            }
