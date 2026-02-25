import os
import logging
from typing import Optional, List
from pathlib import Path

# Desabilitar telemetria do ChromaDB (evita erros de posthog)
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Configurar variáveis de ambiente gRPC antes de importar bibliotecas do Google
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço RAG (Retrieval-Augmented Generation) simplificado.

    Fluxo do endpoint POST /api/v1/chat:
    ┌─────────────┐
    │  Pergunta    │
    │  do usuário  │
    └──────┬──────┘
           │
           ▼
    ┌──────────────────────────────────────────────────┐
    │ 1. EMBEDDING (Google Generative AI)              │
    │    A pergunta é convertida em um vetor numérico  │
    │    usando o modelo de embedding configurado.     │
    └──────┬───────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────┐
    │ 2. BUSCA VETORIAL (ChromaDB)                     │
    │    O vetor da pergunta é comparado com os        │
    │    vetores dos documentos armazenados no banco   │
    │    vetorial. Retorna os K chunks mais similares. │
    │    (similaridade por coseno / distância L2)      │
    └──────┬───────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────┐
    │ 3. GERAÇÃO (Google Gemini LLM)                   │
    │    Os chunks recuperados são inseridos no prompt │
    │    como contexto, junto com a pergunta original. │
    │    O LLM gera uma resposta baseada APENAS no     │
    │    contexto fornecido.                           │
    └──────┬───────────────────────────────────────────┘
           │
           ▼
    ┌─────────────┐
    │  Resposta +  │
    │  Fontes      │
    └─────────────┘
    """

    def __init__(self):
        """Inicializa o serviço RAG com ChromaDB e Google Gemini."""
        self.collection_name = settings.COLLECTION_NAME or settings.RAG_COLLECTION_NAME
        self.chroma_path = Path(settings.CHROMA_DB_PATH)
        if not settings.USE_CHROMA_CLOUD:
            self.chroma_path.mkdir(parents=True, exist_ok=True)

        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY não configurada. Configure a variável de ambiente GOOGLE_API_KEY."
            )

        # Inicializar embeddings com Google (leve, sem torch)
        self.embeddings = self._init_embeddings()

        # Inicializar ChromaDB (banco vetorial)
        self.vectorstore = self._init_vectorstore()

        # Inicializar LLM para geração de respostas
        # max_retries=1 evita loop de retries em 429 que trava o request por minutos
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            max_output_tokens=settings.RAG_MAX_OUTPUT_TOKENS,
            max_retries=1,
            request_timeout=30,
        )

        # Criar retriever (busca por similaridade no banco vetorial)
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.RAG_TOP_K_RESULTS}
        )

        logger.info(
            "RAGService inicializado: model=%s, collection=%s, top_k=%d",
            settings.GEMINI_MODEL,
            self.collection_name,
            settings.RAG_TOP_K_RESULTS,
        )

    def _init_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Inicializa modelo de embedding com retry."""
        embedding_model = settings.EMBEDDING_MODEL
        kwargs = {
            "google_api_key": settings.GOOGLE_API_KEY,
            "request_timeout": 120,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                model = embedding_model if embedding_model.startswith("models/") else "models/embedding-001"
                return GoogleGenerativeAIEmbeddings(model=model, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1 and any(
                    kw in str(e).lower() for kw in ("dns", "timeout", "503")
                ):
                    import time
                    time.sleep(2 * (attempt + 1))
                    kwargs["request_timeout"] = 120 + (attempt * 60)
                    continue
                raise

    def _init_vectorstore(self) -> Chroma:
        """
        Inicializa o ChromaDB vector store.

        O ChromaDB é o banco vetorial que armazena os embeddings dos documentos.
        Quando um documento é indexado, seu texto é convertido em um vetor numérico
        e armazenado aqui. Na hora da busca, a pergunta do usuário também é
        convertida em vetor e comparada com todos os vetores armazenados para
        encontrar os documentos mais similares.
        """
        try:
            if settings.USE_CHROMA_CLOUD:
                import chromadb

                chroma_client = chromadb.CloudClient(
                    api_key=settings.CHROMA_API_KEY,
                    tenant=settings.CHROMA_TENANT,
                    database=settings.CHROMA_DATABASE,
                )
                vectorstore = Chroma(
                    client=chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                )
            else:
                vectorstore = Chroma(
                    persist_directory=str(self.chroma_path),
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name,
                )

            # Placeholder solo para DB local vazio (cloud já tem documentos)
            if not settings.USE_CHROMA_CLOUD:
                collection = vectorstore._collection
                if collection.count() == 0:
                    vectorstore.add_texts(
                        texts=["Nenhum documento foi indexado ainda. Adicione documentos primeiro."],
                        ids=["placeholder"],
                    )

            return vectorstore
        except Exception as e:
            if settings.USE_CHROMA_CLOUD:
                raise  # Não esconder erros de conexão com cloud
            logger.warning("Erro ao abrir ChromaDB local, criando novo: %s", e)
            vectorstore = Chroma(
                persist_directory=str(self.chroma_path),
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
            )
            vectorstore.add_texts(
                texts=["Nenhum documento foi indexado ainda. Adicione documentos primeiro."],
                ids=["placeholder"],
            )
            return vectorstore

    def query(self, question: str) -> dict:
        """
        Processa uma pergunta e retorna resposta com RAG.

        Este é o método principal. O fluxo:
        1. Busca os documentos mais relevantes no banco vetorial (UMA chamada)
        2. Formata o contexto com truncamento para economizar tokens
        3. Envia pergunta + contexto ao LLM (UMA chamada)
        4. Retorna resposta + fontes

        Args:
            question: Pergunta do usuário

        Returns:
            dict com 'answer' e 'sources'
        """
        try:
            # ── Passo 1: Busca vetorial (retriever) ──
            # O retriever converte a pergunta em embedding e busca os
            # K documentos mais próximos no ChromaDB por similaridade.
            docs = self.retriever.invoke(question)

            # ── Passo 2: Montar contexto com truncamento ──
            max_chars = settings.RAG_MAX_CHUNK_CHARS
            context_parts = []
            for doc in docs:
                content = doc.page_content[:max_chars]
                source = doc.metadata.get("source", "Documento desconhecido")
                context_parts.append(f"[Fonte: {source}]\n{content}")

            context = "\n\n---\n\n".join(context_parts) if context_parts else "Nenhum documento relevante encontrado."

            # ── Passo 3: Gerar resposta com o LLM ──
            prompt = _PROMPT_TEMPLATE.format(context=context, question=question)
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            # Extrair fontes únicas
            sources = []
            for doc in docs:
                source = doc.metadata.get("source", "")
                if source and source != "placeholder" and source not in sources:
                    sources.append(source)

            if not sources and "Nenhum documento foi indexado" in answer:
                return {
                    "answer": "Nenhum documento foi indexado ainda. Adicione documentos primeiro para que eu possa responder suas perguntas.",
                    "sources": [],
                }

            return {
                "answer": answer,
                "sources": sources if sources else None,
            }

        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return {
                    "answer": "Erro de autenticação com o serviço de IA. Verifique se a GOOGLE_API_KEY está configurada corretamente.",
                    "sources": None,
                }
            return {
                "answer": f"Ocorreu um erro ao processar sua pergunta: {error_msg}",
                "sources": None,
            }

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ):
        """Adiciona documentos ao vector store."""
        try:
            collection = self.vectorstore._collection
            try:
                collection.delete(ids=["placeholder"])
            except Exception:
                pass

            self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            return True
        except Exception as e:
            raise Exception(f"Erro ao adicionar documentos: {str(e)}")

    def get_collection_info(self) -> dict:
        """Retorna informações sobre a collection atual."""
        try:
            collection = self.vectorstore._collection
            return {
                "collection_name": self.collection_name,
                "total_documents": collection.count(),
                "chroma_path": str(self.chroma_path),
            }
        except Exception as e:
            return {"error": str(e)}


# ── Prompt template otimizado ──
_PROMPT_TEMPLATE = """Você é o assistente do ConcursIA, especializado em concursos públicos e provas como o ENEM.
Você é amigável, didático e ajuda estudantes a entenderem melhor os conteúdos.

Instruções:
- Use as informações do contexto abaixo para formular sua resposta.
- Se o contexto contiver informação relevante, elabore uma resposta completa e bem estruturada.
- Se a informação não estiver disponível no contexto, diga de forma gentil que não encontrou essa informação nos documentos disponíveis, mas tente ajudar com o que sabe sobre o tema.
- Seja acolhedor e encoraje o estudante.

Contexto dos documentos:
{context}

Pergunta do estudante: {question}

Resposta:"""
