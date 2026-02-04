#!/usr/bin/env python3
"""
Script para adicionar questões de exemplo ao banco de dados.
Execute: python scripts/add_sample_questions.py
"""

import sys
import os
from pathlib import Path
import uuid

# Configurar path para a raiz do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports globais com src.
from src.config.database import engine, Base
from src.models.question import Question

# Criar tabelas se não existirem (isso já estava funcionando pelos logs)
Base.metadata.create_all(bind=engine)

SAMPLE_QUESTIONS = [
    {
        "enunciado": "Qual é a fórmula molecular da água?",
        "alternativas": [
            {"letra": "A", "texto": "H2O"},
            {"letra": "B", "texto": "CO2"},
            {"letra": "C", "texto": "O2"},
            {"letra": "D", "texto": "H2O2"},
            {"letra": "E", "texto": "CH4"}
        ],
        "gabarito": "A",
        "ano": 2023,
        "materia": "natureza",
        "topico": "Química",
        "dificuldade": "facil",
        "explicacao": "A água é formada por dois átomos de hidrogênio e um átomo de oxigênio."
    },
    {
        "enunciado": "Qual é o resultado de 2 + 2 × 3?",
        "alternativas": [
            {"letra": "A", "texto": "8"},
            {"letra": "B", "texto": "12"},
            {"letra": "C", "texto": "10"},
            {"letra": "D", "texto": "6"},
            {"letra": "E", "texto": "7"}
        ],
        "gabarito": "A",
        "ano": 2023,
        "materia": "matematica",
        "topico": "Aritmética",
        "dificuldade": "facil",
        "explicacao": "Seguindo a ordem das operações, multiplicação antes da adição: 2 + (2 × 3) = 2 + 6 = 8"
    },
    {
        "enunciado": "Quem escreveu 'Dom Casmurro'?",
        "alternativas": [
            {"letra": "A", "texto": "José de Alencar"},
            {"letra": "B", "texto": "Machado de Assis"},
            {"letra": "C", "texto": "Castro Alves"},
            {"letra": "D", "texto": "Carlos Drummond de Andrade"},
            {"letra": "E", "texto": "Clarice Lispector"}
        ],
        "gabarito": "B",
        "ano": 2023,
        "materia": "linguagens",
        "topico": "Literatura Brasileira",
        "dificuldade": "media",
        "explicacao": "Dom Casmurro é um romance escrito por Machado de Assis, publicado em 1899."
    },
    {
        "enunciado": "Em que ano ocorreu a Proclamação da República no Brasil?",
        "alternativas": [
            {"letra": "A", "texto": "1822"},
            {"letra": "B", "texto": "1888"},
            {"letra": "C", "texto": "1889"},
            {"letra": "D", "texto": "1891"},
            {"letra": "E", "texto": "1900"}
        ],
        "gabarito": "C",
        "ano": 2023,
        "materia": "humanas",
        "topico": "História do Brasil",
        "dificuldade": "facil",
        "explicacao": "A Proclamação da República ocorreu em 15 de novembro de 1889."
    },
    {
        "enunciado": "Qual é a unidade de medida da força no Sistema Internacional?",
        "alternativas": [
            {"letra": "A", "texto": "Joule"},
            {"letra": "B", "texto": "Watt"},
            {"letra": "C", "texto": "Newton"},
            {"letra": "D", "texto": "Pascal"},
            {"letra": "E", "texto": "Coulomb"}
        ],
        "gabarito": "C",
        "ano": 2023,
        "materia": "natureza",
        "topico": "Física",
        "dificuldade": "media",
        "explicacao": "O Newton (N) é a unidade de medida de força no SI, definido como kg·m/s²."
    },
    {
        "enunciado": "Qual é o valor de √64?",
        "alternativas": [
            {"letra": "A", "texto": "6"},
            {"letra": "B", "texto": "7"},
            {"letra": "C", "texto": "8"},
            {"letra": "D", "texto": "9"},
            {"letra": "E", "texto": "10"}
        ],
        "gabarito": "C",
        "ano": 2024,
        "materia": "matematica",
        "topico": "Radiciação",
        "dificuldade": "facil",
        "explicacao": "A raiz quadrada de 64 é 8, pois 8 × 8 = 64."
    },
    {
        "enunciado": "Qual figura de linguagem está presente na frase: 'Aquela mulher é um anjo'?",
        "alternativas": [
            {"letra": "A", "texto": "Metáfora"},
            {"letra": "B", "texto": "Metonímia"},
            {"letra": "C", "texto": "Hipérbole"},
            {"letra": "D", "texto": "Eufemismo"},
            {"letra": "E", "texto": "Antítese"}
        ],
        "gabarito": "A",
        "ano": 2024,
        "materia": "linguagens",
        "topico": "Figuras de Linguagem",
        "dificuldade": "media",
        "explicacao": "Metáfora é uma comparação implícita, onde se atribui características de um ser a outro."
    },
    {
        "enunciado": "Qual foi o principal objetivo das Grandes Navegações?",
        "alternativas": [
            {"letra": "A", "texto": "Evangelização"},
            {"letra": "B", "texto": "Expansão territorial e comercial"},
            {"letra": "C", "texto": "Turismo"},
            {"letra": "D", "texto": "Pesquisa científica"},
            {"letra": "E", "texto": "Migração populacional"}
        ],
        "gabarito": "B",
        "ano": 2024,
        "materia": "humanas",
        "topico": "História Moderna",
        "dificuldade": "media",
        "explicacao": "As Grandes Navegações visavam principalmente expandir territórios e rotas comerciais."
    },
    {
        "enunciado": "Qual organela celular é responsável pela respiração celular?",
        "alternativas": [
            {"letra": "A", "texto": "Núcleo"},
            {"letra": "B", "texto": "Mitocôndria"},
            {"letra": "C", "texto": "Ribossomo"},
            {"letra": "D", "texto": "Cloroplasto"},
            {"letra": "E", "texto": "Vacúolo"}
        ],
        "gabarito": "B",
        "ano": 2024,
        "materia": "natureza",
        "topico": "Biologia Celular",
        "dificuldade": "facil",
        "explicacao": "As mitocôndrias são responsáveis pela respiração celular e produção de ATP."
    },
    {
        "enunciado": "Se f(x) = 2x + 5, qual o valor de f(3)?",
        "alternativas": [
            {"letra": "A", "texto": "8"},
            {"letra": "B", "texto": "9"},
            {"letra": "C", "texto": "10"},
            {"letra": "D", "texto": "11"},
            {"letra": "E", "texto": "13"}
        ],
        "gabarito": "D",
        "ano": 2024,
        "materia": "matematica",
        "topico": "Funções",
        "dificuldade": "facil",
        "explicacao": "f(3) = 2(3) + 5 = 6 + 5 = 11"
    }
]


def add_sample_questions():
    """Adiciona questões de exemplo ao banco."""
    from config.database import SessionLocal

    db = SessionLocal()

    try:
        # Verificar se já existem questões
        existing_count = db.query(Question).count()

        if existing_count > 0:
            print(f"⚠️  Já existem {existing_count} questões no banco.")
            response = input("Deseja adicionar mesmo assim? (s/n): ")
            if response.lower() != 's':
                print("❌ Operação cancelada.")
                return

        added = 0
        for q_data in SAMPLE_QUESTIONS:
            question = Question(
                id=uuid.uuid4(),
                **q_data
            )
            db.add(question)
            added += 1

        db.commit()
        print(f"✅ {added} questões adicionadas com sucesso!")

        # Mostrar estatísticas
        total = db.query(Question).count()
        print(f"\n📊 Total de questões no banco: {total}")

        # Contar por matéria
        from sqlalchemy import func
        stats = db.query(
            Question.materia,
            func.count(Question.id)
        ).group_by(Question.materia).all()

        print("\n📚 Questões por matéria:")
        for materia, count in stats:
            print(f"  - {materia}: {count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar questões: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Adicionando questões de exemplo ao banco...\n")
    add_sample_questions()
