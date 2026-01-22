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
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.config.database import engine, SessionLocal
from src.models.question import Question, Materia, Dificuldade


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
    Retorna estatísticas de inserção.
    """
    stats = {
        "total": len(questions),
        "inserted": 0,
        "errors": 0,
        "by_materia": {},
        "by_ano": {},
    }
    
    batch = []
    
    for i, q_data in enumerate(questions):
        try:
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
        print(f"Erros: {stats['errors']}")
        
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
