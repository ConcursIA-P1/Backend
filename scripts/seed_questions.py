"""
Script para popular o banco de dados com as questões classificadas do ENEM.

Uso:
    python scripts/seed_questions.py

O script irá:
1. Ler o arquivo data/questions_classified.json
2. Inserir todas as questões no banco de dados PostgreSQL
3. Exibir estatísticas de inserção

Pré-requisitos:
- Banco de dados PostgreSQL rodando
- Migrations aplicadas (tabela 'questions' existente)
- Variáveis de ambiente configuradas (.env)
"""

import json
import re
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.config.database import engine, SessionLocal
from src.models.question import Question, Materia, Dificuldade

# Regex para detectar referências de imagem local no enunciado
IMAGE_REF_PATTERN = re.compile(r"\[IMAGEM:\s*[^\]]+\]")

# Tamanho mínimo do enunciado para ser considerado válido
MIN_ENUNCIADO_LENGTH = 20

# Tamanho mínimo do texto de uma alternativa para ser considerada válida
MIN_ALTERNATIVA_LENGTH = 2


# Mapeamento de matérias do JSON para o Enum do banco
MATERIA_MAP = {
    "portugues": Materia.LINGUAGENS,
    "ingles": Materia.LINGUAGENS,
    "espanhol": Materia.LINGUAGENS,
    "historia": Materia.HUMANAS,
    "geografia": Materia.HUMANAS,
    "filosofia_sociologia": Materia.HUMANAS,
    "quimica": Materia.NATUREZA,
    "fisica": Materia.NATUREZA,
    "biologia": Materia.NATUREZA,
    "matematica": Materia.MATEMATICA,
}


def load_questions(file_path: str) -> list[dict]:
    """Carrega questões do arquivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def has_corrupted_text(text: str) -> bool:
    """
    Verifica se um texto contém caracteres de controle que indicam corrupção.
    Caracteres de controle são aqueles no intervalo U+0000–U+001F (exceto \\n, \\r, \\t)
    e U+007F–U+009F.
    """
    for ch in text:
        code = ord(ch)
        if code <= 0x1F and ch not in ('\n', '\r', '\t'):
            return True
        if 0x7F <= code <= 0x9F:
            return True
    return False


def clean_image_references(enunciado: str) -> str:
    """
    Remove referências de imagem local do enunciado.
    Ex: '[IMAGEM: /home/.../question-56.png]' é removido.
    """
    return IMAGE_REF_PATTERN.sub("", enunciado)


def is_valid_question(question_data: dict) -> tuple[bool, str]:
    """
    Valida se uma questão está íntegra o suficiente para ser inserida no banco.
    Retorna (válida, motivo_rejeição).

    Critérios de rejeição:
    - Enunciado com caracteres de controle (texto corrompido)
    - Enunciado muito curto (< MIN_ENUNCIADO_LENGTH caracteres)
    - Alternativas ausentes ou com menos de 2 opções
    - Qualquer alternativa com texto corrompido (caracteres de controle)
    - Qualquer alternativa com texto vazio ou muito curto (< MIN_ALTERNATIVA_LENGTH)
    """
    enunciado = question_data.get("enunciado", "")

    # Verificar texto corrompido no enunciado (antes de limpar imagem)
    if has_corrupted_text(enunciado):
        return False, "enunciado com texto corrompido"

    # Verificar tamanho mínimo do enunciado (após limpar referências de imagem)
    enunciado_limpo = clean_image_references(enunciado).strip()
    if len(enunciado_limpo) < MIN_ENUNCIADO_LENGTH:
        return False, f"enunciado muito curto ({len(enunciado_limpo)} chars)"

    # Verificar alternativas
    alternativas = question_data.get("alternativas", [])
    if len(alternativas) < 2:
        return False, f"poucas alternativas ({len(alternativas)})"

    for alt in alternativas:
        texto = alt.get("texto", "")
        if has_corrupted_text(texto):
            return False, f"alternativa {alt.get('letra', '?')} com texto corrompido"
        if len(texto.strip()) < MIN_ALTERNATIVA_LENGTH:
            return False, f"alternativa {alt.get('letra', '?')} com texto vazio/muito curto"

    return True, ""


def sanitize_question(question_data: dict) -> dict:
    """
    Limpa/sanitiza os dados de uma questão antes da inserção.
    Remove referências de imagem local do enunciado.
    """
    question_data = question_data.copy()
    question_data["enunciado"] = clean_image_references(question_data["enunciado"])
    return question_data


def create_question(db: Session, question_data: dict) -> Question:
    """Cria uma questão no banco de dados."""
    
    # Mapear matéria
    materia_str = question_data.get("materia")
    materia = MATERIA_MAP.get(materia_str) if materia_str else None
    
    # Criar subtópico com a matéria específica (inglês, espanhol, história, etc.)
    subtopico = materia_str if materia_str else None
    
    # Mapear dificuldade (se existir)
    dificuldade_str = question_data.get("dificuldade")
    dificuldade = None
    if dificuldade_str:
        dificuldade_map = {
            "facil": Dificuldade.FACIL,
            "media": Dificuldade.MEDIA,
            "dificil": Dificuldade.DIFICIL,
        }
        dificuldade = dificuldade_map.get(dificuldade_str.lower())
    
    # Criar objeto Question
    db_question = Question(
        enunciado=question_data["enunciado"],
        alternativas=question_data["alternativas"],
        gabarito=question_data["gabarito"],
        ano=question_data["ano"],
        materia=materia,
        topico=question_data.get("topico"),
        subtopico=subtopico,
        dificuldade=dificuldade,
        banca=question_data.get("banca", "INEP"),
        prova=question_data.get("prova"),
        numero_questao=question_data.get("numero_questao"),
        explicacao=question_data.get("explicacao"),
        imagem_url=question_data.get("imagem_url"),
        tags=question_data.get("tags"),
    )
    
    return db_question


def seed_questions(db: Session, questions: list[dict], batch_size: int = 100) -> dict:
    """
    Insere questões no banco em lotes.
    Filtra questões com texto corrompido ou incompleto.
    Retorna estatísticas de inserção.
    """
    stats = {
        "total": len(questions),
        "inserted": 0,
        "skipped": 0,
        "errors": 0,
        "by_materia": {},
        "by_ano": {},
        "skip_reasons": {},
    }
    
    batch = []
    
    for i, q_data in enumerate(questions):
        try:
            # Validar questão
            valid, reason = is_valid_question(q_data)
            if not valid:
                stats["skipped"] += 1
                stats["skip_reasons"][reason] = stats["skip_reasons"].get(reason, 0) + 1
                prova = q_data.get("prova", "?")
                num = q_data.get("numero_questao", "?")
                print(f"  ⚠️  Questão ignorada ({prova}, nº {num}): {reason}")
                continue

            # Sanitizar questão (remover referências de imagem, etc.)
            q_data = sanitize_question(q_data)

            question = create_question(db, q_data)
            batch.append(question)
            
            # Estatísticas
            materia = q_data.get("materia", "desconhecida")
            ano = q_data.get("ano", 0)
            
            stats["by_materia"][materia] = stats["by_materia"].get(materia, 0) + 1
            stats["by_ano"][ano] = stats["by_ano"].get(ano, 0) + 1
            
            # Inserir em lotes
            if len(batch) >= batch_size:
                db.add_all(batch)
                db.commit()
                stats["inserted"] += len(batch)
                print(f"  Inseridas: {stats['inserted']}/{stats['total']}")
                batch = []
                
        except Exception as e:
            stats["errors"] += 1
            print(f"  ❌ Erro na questão {i + 1}: {e}")
    
    # Inserir lote restante
    if batch:
        db.add_all(batch)
        db.commit()
        stats["inserted"] += len(batch)
        print(f"  Inseridas: {stats['inserted']}/{stats['total']}")
    
    return stats


def clear_questions(db: Session):
    """Remove todas as questões do banco (para reprocessamento)."""
    count = db.query(Question).count()
    if count > 0:
        db.query(Question).delete()
        db.commit()
        print(f"  🗑️  Removidas {count} questões existentes")


def main():
    print("=" * 60)
    print("SEED DE QUESTÕES ENEM")
    print("=" * 60)
    
    # Caminho do arquivo
    data_file = project_root / "data" / "questions_classified.json"
    
    if not data_file.exists():
        print(f"❌ Arquivo não encontrado: {data_file}")
        print("   Execute primeiro: python scripts/classify_questions.py")
        sys.exit(1)
    
    print(f"Arquivo: {data_file}")
    print()
    
    # Carregar questões
    print("📂 Carregando questões...")
    questions = load_questions(str(data_file))
    print(f"   {len(questions)} questões carregadas")
    print()
    
    # Conectar ao banco
    print("🔌 Conectando ao banco de dados...")
    db = SessionLocal()
    
    try:
        # Verificar se há questões existentes
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"   ⚠️  Encontradas {existing_count} questões existentes")
            response = input("   Deseja limpar e reinserir? (s/N): ").strip().lower()
            if response == 's':
                clear_questions(db)
            else:
                print("   Operação cancelada.")
                return
        
        print()
        print("📝 Inserindo questões...")
        stats = seed_questions(db, questions)
        
        print()
        print("=" * 60)
        print("ESTATÍSTICAS")
        print("=" * 60)
        print(f"Total processadas: {stats['total']}")
        print(f"Inseridas com sucesso: {stats['inserted']}")
        print(f"Ignoradas (defeituosas): {stats['skipped']}")
        print(f"Erros: {stats['errors']}")
        
        if stats["skip_reasons"]:
            print()
            print("Motivos de rejeição:")
            for reason in sorted(stats["skip_reasons"].keys()):
                print(f"  {reason}: {stats['skip_reasons'][reason]}")
        
        print()
        print("Por matéria:")
        for materia in sorted(stats["by_materia"].keys()):
            print(f"  {materia}: {stats['by_materia'][materia]}")
        
        print()
        print("Por ano:")
        for ano in sorted(stats["by_ano"].keys()):
            print(f"  {ano}: {stats['by_ano'][ano]}")
        
        print()
        print("✅ Seed concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
