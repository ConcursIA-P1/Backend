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
            # Mantém o marcador de imagem no texto para referência
            img_path = item.get("content", "")
            # Tenta limpar o caminho para ficar legível no texto
            clean_name = os.path.basename(img_path)
            texts.append(f"[IMAGEM: {clean_name}]")
    
    full_text = "".join(texts)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    return full_text


def extract_alternative_text(content_list: list[dict]) -> str:
    """Extrai texto de uma alternativa."""
    text = join_content(content_list)
    return text.lstrip('\t ').strip()


def find_correct_answer(alternatives: dict) -> Optional[str]:
    """Encontra a letra da alternativa correta."""
    for key, alt in alternatives.items():
        if alt.get("correct", False):
            return alt.get("alternative", "").upper()
    return None


def extract_image_path(content_list: list[dict]) -> Optional[str]:
    """
    Procura por uma imagem no conteúdo e retorna o caminho relativo limpo.
    Ex: output_2017_d1_prova/img/question-16.png
    """
    for item in content_list:
        if item.get("type") == "image":
            raw_path = item.get("content", "")
            # Regex para pegar apenas a parte 'output_XXXX...' do caminho
            # Isso remove o '/home/usuario/...' que vem do JSON original
            match = re.search(r'(output_\d{4}_d\d_prova/img/.*)', raw_path)
            if match:
                return match.group(1)
    return None


def process_question(question: dict, ano: int, dia: int, prova_folder: str) -> dict:
    """Processa uma questão para o formato do banco de dados."""
    
    enunciado = join_content(question.get("content", []))
    imagem_url = extract_image_path(question.get("content", []))
    
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
    
    gabarito = find_correct_answer(raw_alternatives)
    
    processed = {
        "enunciado": enunciado,
        "alternativas": alternativas,
        "gabarito": gabarito,
        "ano": ano,
        "prova": f"ENEM {ano} - Dia {dia}",
        "numero_questao": question.get("number"),
        "banca": "INEP",
        "materia": None,
        "topico": None,
        "dificuldade": None,
        "explicacao": None,
        "imagem_url": imagem_url, # Agora estamos salvando o caminho aqui!
        "tags": None
    }
    
    return processed


def process_all_exams(data_dir: str) -> list[dict]:
    """Processa todas as provas do diretório data/."""
    all_questions = []
    data_path = Path(data_dir)
    
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
                
                if processed["enunciado"] and processed["alternativas"] and processed["gabarito"]:
                    all_questions.append(processed)
                else:
                    print(f"    ⚠️  Questão {question.get('number')} inválida - dados faltando")
            except Exception as e:
                print(f"    ❌ Erro na questão {question.get('number')}: {e}")
    
    return all_questions


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print("=" * 60)
    print("PROCESSADOR DE QUESTÕES ENEM")
    print("=" * 60)
    print(f"Diretório de dados: {data_dir}")
    print()
    
    all_questions = process_all_exams(data_dir)
    
    print()
    print("=" * 60)
    print(f"TOTAL DE QUESTÕES PROCESSADAS: {len(all_questions)}")
    print("=" * 60)
    
    output_file = data_dir / "questions_processed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Arquivo salvo: {output_file}")

if __name__ == "__main__":
    main()