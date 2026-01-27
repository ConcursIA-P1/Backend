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
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.config.database import engine, SessionLocal
from src.models.question import Question, Materia, Dificuldade

# Mapeamento de matérias
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
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_question(db: Session, question_data: dict) -> Question:
    """Cria uma questão no banco de dados."""
    
    materia_str = question_data.get("materia")
    materia = MATERIA_MAP.get(materia_str) if materia_str else None
    subtopico = materia_str if materia_str else None
    
    dificuldade_str = question_data.get("dificuldade")
    dificuldade = None
    if dificuldade_str:
        dificuldade_map = {
            "facil": Dificuldade.FACIL,
            "media": Dificuldade.MEDIA,
            "dificil": Dificuldade.DIFICIL,
        }
        dificuldade = dificuldade_map.get(dificuldade_str.lower())
    
    # --- LOGICA DE IMAGEM ADICIONADA AQUI ---
    imagem_blob = None
    imagem_url = question_data.get("imagem_url")
    
    if imagem_url:
        # Constrói o caminho completo: /app/data/ + output_.../img/...
        img_full_path = project_root / "data" / imagem_url
        
        if img_full_path.exists():
            try:
                with open(img_full_path, "rb") as img_file:
                    imagem_blob = img_file.read()
                # Opcional: comentar o print para não poluir o log se forem muitas imagens
                # print(f"   📸 Imagem carregada: {imagem_url}") 
            except Exception as e:
                print(f"   ❌ Erro ao ler imagem {img_full_path}: {e}")
        else:
            # Apenas avisa, não para o script
            print(f"   ⚠️  Arquivo de imagem não encontrado: {img_full_path}")
    # ----------------------------------------

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
        imagem_url=imagem_url, # Mantemos o path relativo
        imagem_blob=imagem_blob, # Salvamos o binário
        tags=question_data.get("tags"),
    )
    
    return db_question

def seed_questions(db: Session, questions: list[dict], batch_size: int = 100) -> dict:
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
            
            materia = q_data.get("materia", "desconhecida")
            ano = q_data.get("ano", 0)
            
            stats["by_materia"][materia] = stats["by_materia"].get(materia, 0) + 1
            stats["by_ano"][ano] = stats["by_ano"].get(ano, 0) + 1
            
            if len(batch) >= batch_size:
                db.add_all(batch)
                db.commit()
                stats["inserted"] += len(batch)
                print(f"  Inseridas: {stats['inserted']}/{stats['total']}")
                batch = []
                
        except Exception as e:
            stats["errors"] += 1
            print(f"  ❌ Erro na questão {i + 1}: {e}")
    
    if batch:
        db.add_all(batch)
        db.commit()
        stats["inserted"] += len(batch)
        print(f"  Inseridas: {stats['inserted']}/{stats['total']}")
    
    return stats

def clear_questions(db: Session):
    count = db.query(Question).count()
    if count > 0:
        db.query(Question).delete()
        db.commit()
        print(f"  🗑️  Removidas {count} questões existentes")

def main():
    print("=" * 60)
    print("SEED DE QUESTÕES ENEM")
    print("=" * 60)
    
    data_file = project_root / "data" / "questions_classified.json"
    
    # Se o classificado não existir, tenta o processado
    if not data_file.exists():
        print(f"⚠️  'questions_classified.json' não encontrado.")
        print(f"    Tentando 'questions_processed.json' (sem classificação de IA)...")
        data_file = project_root / "data" / "questions_processed.json"
        
    if not data_file.exists():
        print(f"❌ Nenhum arquivo de dados encontrado em {project_root / 'data'}")
        sys.exit(1)
    
    print(f"Arquivo: {data_file}")
    print("📂 Carregando questões...")
    questions = load_questions(str(data_file))
    print(f"   {len(questions)} questões carregadas")
    print()
    
    print("🔌 Conectando ao banco de dados...")
    db = SessionLocal()
    
    try:
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"   ⚠️  Encontradas {existing_count} questões existentes")
            
            # Verifica flag --force ou modo não interativo
            force_mode = "--force" in sys.argv
            
            if force_mode:
                print("   🚀 Modo FORCE: Limpando banco...")
                clear_questions(db)
            else:
                if sys.stdin.isatty():
                    response = input("   Deseja limpar e reinserir? (s/N): ").strip().lower()
                    if response == 's':
                        clear_questions(db)
                    else:
                        print("   Operação cancelada.")
                        return
                else:
                    print("   🤖 Modo não-interativo: Mantendo dados existentes.")
                    return
        
        print()
        print("📝 Inserindo questões...")
        stats = seed_questions(db, questions)
        
        print()
        print("=" * 60)
        print("ESTATÍSTICAS")
        print(f"Total: {stats['total']} | Inseridas: {stats['inserted']} | Erros: {stats['errors']}")
        print("✅ Seed concluído!")
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()