#!/usr/bin/env python3
"""
Script de ingestão para ChromaDB.

Processa as questões do ENEM (JSON) e o edital 2024 (PDF),
gera embeddings com Google Gemini, e armazena no ChromaDB Cloud.

Uso:
    python scripts/ingest.py                 # Ingere tudo
    python scripts/ingest.py --questions     # Apenas questões
    python scripts/ingest.py --pdf           # Apenas PDF
    python scripts/ingest.py --skip 865      # Pula as primeiras 865 questões (retoma)
    python scripts/ingest.py --local         # Usa ChromaDB local ao invés de cloud
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path

# Adicionar o diretório raiz ao path para importar settings
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Constantes ──
DATA_DIR = ROOT / "data"
QUESTIONS_FILE = DATA_DIR / "questions_classified.json"
PDF_FILE = DATA_DIR / "EDITAL-ENEM-2024.pdf"

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "enem_documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

BATCH_SIZE = 5  # Batch pequeno: free tier permite ~100 embed requests/min
DELAY_BETWEEN_BATCHES = 4  # Segundos entre batches (~12 req/min = 60 req/5min)
MAX_RETRIES = 5  # Retries por batch em caso de 429
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def get_embeddings():
    """Inicializa embeddings do Google Gemini."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não encontrada no .env")
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )


def get_chroma_client(local: bool = False):
    """Retorna ChromaDB client (cloud ou local)."""
    if local:
        return None  # Langchain Chroma cria client local automaticamente
    return chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY", ""),
        tenant=os.getenv("CHROMA_TENANT", ""),
        database=os.getenv("CHROMA_DATABASE", ""),
    )


def format_question(q: dict) -> tuple[str, dict]:
    """
    Formata uma questão em texto + metadados para indexação.

    Returns:
        (texto_formatado, metadados)
    """
    # Montar texto completo da questão
    parts = [f"[ENEM {q['ano']} - {q.get('materia', 'geral').upper()}]"]
    parts.append(f"Questão {q.get('numero_questao', '?')}:")
    parts.append(q["enunciado"])

    # Alternativas
    for alt in q.get("alternativas", []):
        parts.append(f"  {alt['letra']}) {alt['texto']}")

    parts.append(f"Gabarito: {q['gabarito']}")

    if q.get("explicacao"):
        parts.append(f"Explicação: {q['explicacao']}")

    text = "\n".join(parts)

    # Metadados
    metadata = {
        "source": f"enem_{q['ano']}",
        "type": "questao",
        "ano": q["ano"],
        "materia": q.get("materia", ""),
        "prova": q.get("prova", ""),
        "numero_questao": q.get("numero_questao", 0),
        "gabarito": q["gabarito"],
        "banca": q.get("banca", "INEP"),
    }

    return text, metadata


def generate_id(text: str) -> str:
    """Gera um ID determinístico baseado no conteúdo."""
    return hashlib.md5(text.encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks com overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def extract_pdf_text(pdf_path: Path) -> str:
    """Extrai texto de um PDF."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        logger.error("PyPDF2 não instalado. Execute: pip install PyPDF2")
        sys.exit(1)

    reader = PdfReader(str(pdf_path))
    text_parts = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            text_parts.append(page_text.strip())
    full_text = "\n\n".join(text_parts)
    logger.info("PDF: %d páginas, %d caracteres extraídos", len(reader.pages), len(full_text))
    return full_text


def ingest_in_batches(vectorstore, texts: list[str], metadatas: list[dict], ids: list[str], label: str):
    """
    Adiciona documentos ao vectorstore em batches com rate limiting e retry.
    """
    total = len(texts)
    ingested = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_metas = metadatas[i:i + BATCH_SIZE]
        batch_ids = ids[i:i + BATCH_SIZE]

        # Retry com backoff exponencial
        for attempt in range(MAX_RETRIES):
            try:
                vectorstore.add_texts(
                    texts=batch_texts,
                    metadatas=batch_metas,
                    ids=batch_ids,
                )
                ingested += len(batch_texts)
                pct = (ingested / total) * 100
                logger.info("[%s] %d/%d (%.0f%%)", label, ingested, total, pct)
                break
            except Exception as e:
                if "429" in str(e) and attempt < MAX_RETRIES - 1:
                    wait = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s
                    logger.warning("[%s] Rate limit no batch %d, aguardando %ds (tentativa %d/%d)",
                                   label, i // BATCH_SIZE + 1, wait, attempt + 1, MAX_RETRIES)
                    time.sleep(wait)
                else:
                    errors += len(batch_texts)
                    logger.error("[%s] Erro no batch %d: %s", label, i // BATCH_SIZE + 1, str(e)[:100])
                    break

        if i + BATCH_SIZE < total:
            time.sleep(DELAY_BETWEEN_BATCHES)

    logger.info("[%s] Concluído: %d ok, %d erros", label, ingested, errors)
    return ingested, errors


def ingest_questions(vectorstore, skip: int = 0):
    """Processa e indexa questões do ENEM."""
    if not QUESTIONS_FILE.exists():
        logger.error("Arquivo não encontrado: %s", QUESTIONS_FILE)
        return

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    logger.info("Carregadas %d questões de %s", len(questions), QUESTIONS_FILE.name)

    texts, metadatas, ids = [], [], []
    for q in questions:
        text, meta = format_question(q)
        doc_id = generate_id(text)
        texts.append(text)
        metadatas.append(meta)
        ids.append(doc_id)

    if skip > 0:
        logger.info("Pulando as primeiras %d questões já indexadas", skip)
        texts = texts[skip:]
        metadatas = metadatas[skip:]
        ids = ids[skip:]
        logger.info("Restam %d questões para indexar", len(texts))

    # Estatísticas
    anos = {}
    for m in metadatas:
        ano = m["ano"]
        anos[ano] = anos.get(ano, 0) + 1
    logger.info("Questões por ano: %s", dict(sorted(anos.items())))

    return ingest_in_batches(vectorstore, texts, metadatas, ids, "Questões")


def ingest_pdf(vectorstore):
    """Processa e indexa o edital do ENEM 2024."""
    if not PDF_FILE.exists():
        logger.error("Arquivo não encontrado: %s", PDF_FILE)
        return

    full_text = extract_pdf_text(PDF_FILE)
    chunks = chunk_text(full_text)
    logger.info("Edital dividido em %d chunks", len(chunks))

    texts, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        doc_id = generate_id(f"edital_2024_chunk_{i}_{chunk[:50]}")
        texts.append(chunk)
        metadatas.append({
            "source": "edital_enem_2024",
            "type": "edital",
            "chunk_index": i,
            "total_chunks": len(chunks),
        })
        ids.append(doc_id)

    return ingest_in_batches(vectorstore, texts, metadatas, ids, "Edital PDF")


def main():
    parser = argparse.ArgumentParser(description="Ingestão de dados para ChromaDB")
    parser.add_argument("--questions", action="store_true", help="Indexar apenas questões")
    parser.add_argument("--pdf", action="store_true", help="Indexar apenas PDF")
    parser.add_argument("--skip", type=int, default=0, help="Pular as primeiras N questões (para retomar)")
    parser.add_argument("--local", action="store_true", help="Usar ChromaDB local")
    args = parser.parse_args()

    # Se nenhum flag específico, ingere tudo
    do_all = not args.questions and not args.pdf

    logger.info("=" * 60)
    logger.info("INGESTÃO ChromaDB")
    logger.info("Collection: %s", COLLECTION_NAME)
    logger.info("Embedding: %s", EMBEDDING_MODEL)
    logger.info("Modo: %s", "local" if args.local else "cloud")
    logger.info("=" * 60)

    # Inicializar embeddings
    embeddings = get_embeddings()
    logger.info("✅ Embeddings Gemini inicializados")

    # Inicializar ChromaDB + Langchain wrapper
    if args.local:
        chroma_path = str(ROOT / "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        vectorstore = Chroma(
            persist_directory=chroma_path,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
    else:
        client = get_chroma_client()
        vectorstore = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )
    logger.info("✅ ChromaDB conectado")

    total_ingested = 0
    total_errors = 0

    # Questões
    if do_all or args.questions:
        result = ingest_questions(vectorstore, skip=args.skip)
        if result:
            total_ingested += result[0]
            total_errors += result[1]

    # PDF
    if do_all or args.pdf:
        result = ingest_pdf(vectorstore)
        if result:
            total_ingested += result[0]
            total_errors += result[1]

    # Resumo
    logger.info("=" * 60)
    logger.info("RESUMO")
    logger.info("  Documentos indexados: %d", total_ingested)
    logger.info("  Erros: %d", total_errors)

    # Verificar collection
    try:
        collection = vectorstore._collection
        logger.info("  Total na collection: %d", collection.count())
    except Exception:
        pass
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
