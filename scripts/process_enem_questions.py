"""
Script para processar os JSONs das provas do ENEM e converter
para o formato esperado pelo banco de dados.

Uso:
    python scripts/process_enem_questions.py

O script irá:
1. Ler todos os output.json das pastas data/output_*
2. Processar cada questão (juntar enunciado, formatar alternativas, extrair gabarito)
3. Gerar um arquivo unificado: data/questions_processed.json
"""

import json
import os
import re
from pathlib import Path
from typing import Optional


def extract_year_and_day(folder_name: str) -> tuple[int, int]:
    """Extrai ano e dia da pasta. Ex: 'output_2017_d1_prova' -> (2017, 1)"""
    match = re.match(r'output_(\d{4})_d(\d)_prova', folder_name)
    if match:
        return int(match.group(1)), int(match.group(2))
    raise ValueError(f"Formato de pasta inválido: {folder_name}")


def join_content(content_list: list[dict]) -> str:
    """Junta os textos fragmentados do conteúdo em uma string única."""
    texts = []
    for item in content_list:
        if item.get("type") == "text":
            texts.append(item.get("content", ""))
        elif item.get("type") == "image":
            # Marca onde há imagem (pode ser processado depois)
            img_path = item.get("content", "")
            texts.append(f"[IMAGEM: {img_path}]")
    
    # Junta e limpa espaços extras
    full_text = "".join(texts)
    # Remove espaços múltiplos e tabs extras
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    return full_text


def extract_alternative_text(content_list: list[dict]) -> str:
    """Extrai texto de uma alternativa."""
    text = join_content(content_list)
    # Remove tab e espaços iniciais das alternativas
    return text.lstrip('\t ').strip()


def find_correct_answer(alternatives: dict) -> Optional[str]:
    """Encontra a letra da alternativa correta."""
    for key, alt in alternatives.items():
        if alt.get("correct", False):
            return alt.get("alternative", "").upper()
    return None


def process_question(question: dict, ano: int, dia: int, prova_folder: str) -> dict:
    """Processa uma questão para o formato do banco de dados."""
    
    # Juntar enunciado
    enunciado = join_content(question.get("content", []))
    
    # Processar alternativas
    raw_alternatives = question.get("alternatives", {})
    alternativas = []
    
    for key in sorted(raw_alternatives.keys(), key=int):
        alt = raw_alternatives[key]
        letra = alt.get("alternative", "").upper()
        texto = extract_alternative_text(alt.get("content", []))
        alternativas.append({
            "letra": letra,
            "texto": texto
        })
    
    # Encontrar gabarito
    gabarito = find_correct_answer(raw_alternatives)
    
    # Montar questão processada
    processed = {
        "enunciado": enunciado,
        "alternativas": alternativas,
        "gabarito": gabarito,
        "ano": ano,
        "prova": f"ENEM {ano} - Dia {dia}",
        "numero_questao": question.get("number"),
        "banca": "INEP",
        # Campos opcionais (podem ser preenchidos depois)
        "materia": None,
        "topico": None,
        "dificuldade": None,
        "explicacao": None,
        "imagem_url": None,
        "tags": None
    }
    
    return processed


def process_all_exams(data_dir: str) -> list[dict]:
    """Processa todas as provas do diretório data/."""
    all_questions = []
    data_path = Path(data_dir)
    
    # Encontrar todas as pastas de prova
    exam_folders = sorted([
        d for d in data_path.iterdir() 
        if d.is_dir() and d.name.startswith("output_")
    ])
    
    print(f"Encontradas {len(exam_folders)} provas para processar")
    
    for folder in exam_folders:
        output_file = folder / "output.json"
        
        if not output_file.exists():
            print(f"  ⚠️  {folder.name}: output.json não encontrado")
            continue
        
        try:
            ano, dia = extract_year_and_day(folder.name)
        except ValueError as e:
            print(f"  ⚠️  {folder.name}: {e}")
            continue
        
        print(f"  📄 Processando {folder.name} (Ano: {ano}, Dia: {dia})...")
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = data.get("data", [])
        
        for question in questions:
            try:
                processed = process_question(question, ano, dia, folder.name)
                
                # Validar questão mínima
                if processed["enunciado"] and processed["alternativas"] and processed["gabarito"]:
                    all_questions.append(processed)
                else:
                    print(f"    ⚠️  Questão {question.get('number')} inválida - dados faltando")
            except Exception as e:
                print(f"    ❌ Erro na questão {question.get('number')}: {e}")
    
    return all_questions


def main():
    # Caminho do diretório data
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print("=" * 60)
    print("PROCESSADOR DE QUESTÕES ENEM")
    print("=" * 60)
    print(f"Diretório de dados: {data_dir}")
    print()
    
    # Processar todas as provas
    all_questions = process_all_exams(data_dir)
    
    print()
    print("=" * 60)
    print(f"TOTAL DE QUESTÕES PROCESSADAS: {len(all_questions)}")
    print("=" * 60)
    
    # Estatísticas por ano
    by_year = {}
    for q in all_questions:
        ano = q["ano"]
        by_year[ano] = by_year.get(ano, 0) + 1
    
    print("\nQuestões por ano:")
    for ano in sorted(by_year.keys()):
        print(f"  {ano}: {by_year[ano]} questões")
    
    # Salvar arquivo processado
    output_file = data_dir / "questions_processed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Arquivo salvo: {output_file}")
    
    # Mostrar exemplo de questão processada
    if all_questions:
        print("\n" + "=" * 60)
        print("EXEMPLO DE QUESTÃO PROCESSADA:")
        print("=" * 60)
        example = all_questions[0]
        print(json.dumps(example, ensure_ascii=False, indent=2)[:1500] + "...")


if __name__ == "__main__":
    main()
