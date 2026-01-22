"""
Script para classificar as questões do ENEM por matéria e tópico.

Usa:
1. Estrutura conhecida da prova do ENEM (numeração das questões)
2. Análise de palavras-chave para identificar tópicos
3. Heurísticas para casos específicos

Estrutura do ENEM:
- Dia 1: Linguagens (questões 1-45) + Ciências Humanas (questões 46-90)
- Dia 2: Ciências da Natureza (questões 91-135) + Matemática (questões 136-180)

Observação: A numeração pode variar ligeiramente entre anos.
"""

import json
import re
from pathlib import Path
from typing import Optional


# ============== CONFIGURAÇÃO DE MATÉRIAS E TÓPICOS ==============

MATERIAS_DIA1_LINGUAGENS = {
    "ingles": {
        "keywords": ["the", "was", "were", "is", "are", "has", "have", "will", "would", "could", "should"],
        "min_english_ratio": 0.4  # 40% das palavras em inglês
    },
    "espanhol": {
        "keywords": ["el", "la", "los", "las", "que", "por", "para", "con", "una", "uno", "está", "están", "fue", "son"],
        "min_spanish_ratio": 0.3
    },
    "portugues": {
        # Default para linguagens se não for inglês/espanhol
    }
}

# Tópicos por matéria
TOPICOS = {
    "ingles": [
        ("interpretacao_texto", ["text", "according", "author", "passage", "article"]),
        ("vocabulario", ["meaning", "word", "vocabulary", "expression"]),
        ("gramatica", ["grammar", "verb", "tense", "pronoun"]),
    ],
    "espanhol": [
        ("interpretacao_texto", ["texto", "según", "autor", "fragmento"]),
        ("vocabulario", ["significado", "palabra", "expresión"]),
        ("gramatica", ["verbo", "gramática", "conjugación"]),
    ],
    "portugues": [
        ("interpretacao_texto", ["texto", "autor", "narrador", "leitor", "leitura"]),
        ("literatura", ["poema", "poeta", "romance", "literário", "literatura", "modernismo", "romantismo", "barroco", "arcadismo"]),
        ("gramatica", ["gramática", "sintaxe", "morfologia", "semântica", "fonologia"]),
        ("generos_textuais", ["gênero", "charge", "tirinha", "propaganda", "editorial", "crônica", "conto"]),
        ("variacao_linguistica", ["variação", "dialeto", "norma", "coloquial", "formal", "informal"]),
        ("figuras_linguagem", ["metáfora", "metonímia", "ironia", "hipérbole", "antítese"]),
        ("funcoes_linguagem", ["função", "emotiva", "referencial", "poética", "fática", "metalinguística"]),
        ("intertextualidade", ["intertextualidade", "paródia", "paráfrase", "citação"]),
        ("artes", ["arte", "pintura", "escultura", "música", "teatro", "cinema", "dança"]),
    ],
    "historia": [
        ("brasil_colonial", ["colonial", "colônia", "escravidão", "engenho", "bandeirantes", "jesuítas"]),
        ("brasil_imperial", ["império", "imperial", "dom pedro", "independência", "regência"]),
        ("brasil_republicano", ["república", "vargas", "ditadura", "militar", "democracia", "golpe"]),
        ("antiguidade", ["grécia", "roma", "egito", "mesopotâmia", "antiguidade", "antigo"]),
        ("idade_media", ["medieval", "feudalismo", "cruzadas", "igreja medieval"]),
        ("idade_moderna", ["renascimento", "reforma", "absolutismo", "mercantilismo", "iluminismo"]),
        ("revolucoes", ["revolução", "francesa", "industrial", "americana", "russa"]),
        ("guerras_mundiais", ["guerra mundial", "nazismo", "fascismo", "hitler", "holocausto"]),
        ("guerra_fria", ["guerra fria", "urss", "soviético", "capitalismo", "socialismo", "comunismo"]),
        ("africa_asia", ["áfrica", "ásia", "descolonização", "apartheid", "imperialismo"]),
        ("movimentos_sociais", ["movimento", "feminismo", "negro", "trabalhador", "sindical"]),
    ],
    "geografia": [
        ("cartografia", ["mapa", "escala", "projeção", "cartografia", "coordenadas", "latitude", "longitude"]),
        ("clima", ["clima", "climático", "temperatura", "precipitação", "umidade", "massas de ar"]),
        ("geomorfologia", ["relevo", "erosão", "solo", "rocha", "placa tectônica", "vulcão"]),
        ("hidrografia", ["rio", "bacia", "hidrografia", "água", "aquífero", "nascente"]),
        ("vegetacao", ["bioma", "vegetação", "floresta", "cerrado", "caatinga", "mata atlântica", "amazônia"]),
        ("urbanizacao", ["cidade", "urbano", "urbanização", "metrópole", "favela", "periferia"]),
        ("populacao", ["população", "demográfico", "migração", "êxodo", "natalidade", "mortalidade"]),
        ("agricultura", ["agricultura", "agrário", "agronegócio", "reforma agrária", "latifúndio"]),
        ("industria", ["indústria", "industrial", "industrialização", "manufatura"]),
        ("globalizacao", ["globalização", "multinacional", "comércio internacional", "blocos econômicos"]),
        ("meio_ambiente", ["ambiental", "sustentável", "desmatamento", "poluição", "aquecimento"]),
        ("energia", ["energia", "petróleo", "renovável", "hidrelétrica", "nuclear", "eólica", "solar"]),
        ("geopolitica", ["geopolítica", "conflito", "fronteira", "território", "soberania"]),
    ],
    "filosofia_sociologia": [
        ("filosofia_antiga", ["sócrates", "platão", "aristóteles", "grécia antiga"]),
        ("filosofia_moderna", ["descartes", "kant", "hegel", "iluminismo"]),
        ("filosofia_contemporanea", ["nietzsche", "marx", "foucault", "existencialismo"]),
        ("etica", ["ética", "moral", "valor", "virtude"]),
        ("politica", ["estado", "poder", "democracia", "cidadania", "direitos"]),
        ("sociologia_classica", ["durkheim", "weber", "marx", "sociologia"]),
        ("cultura_sociedade", ["cultura", "identidade", "ideologia", "alienação"]),
        ("trabalho", ["trabalho", "capitalismo", "classe social", "proletariado"]),
    ],
    "quimica": [
        ("quimica_geral", ["átomo", "elemento", "tabela periódica", "ligação química"]),
        ("quimica_organica", ["orgânico", "carbono", "hidrocarboneto", "álcool", "éster", "amina"]),
        ("quimica_inorganica", ["inorgânico", "ácido", "base", "sal", "óxido"]),
        ("fisico_quimica", ["equilíbrio", "cinética", "termodinâmica", "eletroquímica"]),
        ("estequiometria", ["mol", "massa molar", "estequiometria", "reagente", "produto"]),
        ("solucoes", ["solução", "concentração", "diluição", "solubilidade"]),
        ("reacoes", ["reação", "oxidação", "redução", "combustão"]),
        ("radioatividade", ["radioativo", "núcleo", "decaimento", "meia-vida"]),
        ("quimica_ambiental", ["poluição", "chuva ácida", "ozônio", "efeito estufa"]),
    ],
    "fisica": [
        ("mecanica", ["força", "movimento", "velocidade", "aceleração", "newton", "atrito"]),
        ("termodinamica", ["calor", "temperatura", "térmica", "entropia", "termodinâmica"]),
        ("ondulatoria", ["onda", "frequência", "som", "luz", "interferência", "difração"]),
        ("optica", ["óptica", "espelho", "lente", "refração", "reflexão"]),
        ("eletricidade", ["elétrico", "corrente", "tensão", "resistência", "circuito"]),
        ("magnetismo", ["magnético", "ímã", "campo magnético", "indução"]),
        ("eletromagnetismo", ["eletromagnético", "maxwell", "radiação"]),
        ("fisica_moderna", ["quântico", "relatividade", "einstein", "fóton"]),
        ("hidrostatica", ["pressão", "fluido", "empuxo", "hidrostática"]),
        ("gravitacao", ["gravidade", "gravitacional", "planeta", "órbita"]),
    ],
    "biologia": [
        ("citologia", ["célula", "membrana", "núcleo", "mitocôndria", "organela"]),
        ("genetica", ["gene", "dna", "rna", "hereditário", "cromossomo", "mutação"]),
        ("evolucao", ["evolução", "darwin", "seleção natural", "adaptação", "especiação"]),
        ("ecologia", ["ecologia", "ecossistema", "cadeia alimentar", "nicho", "habitat"]),
        ("fisiologia_humana", ["coração", "sangue", "digestão", "respiração", "hormônio"]),
        ("fisiologia_vegetal", ["fotossíntese", "planta", "vegetal", "clorofila"]),
        ("zoologia", ["animal", "vertebrado", "invertebrado", "mamífero", "inseto"]),
        ("botanica", ["planta", "flor", "fruto", "semente", "raiz"]),
        ("microbiologia", ["bactéria", "vírus", "fungo", "protozoário", "microorganismo"]),
        ("biotecnologia", ["transgênico", "clonagem", "engenharia genética", "biotecnologia"]),
        ("saude", ["doença", "vacina", "imunidade", "epidemia", "saúde pública"]),
    ],
    "matematica": [
        ("algebra", ["equação", "inequação", "polinômio", "fatoração", "expressão algébrica"]),
        ("funcoes", ["função", "gráfico", "domínio", "imagem", "exponencial", "logaritmo"]),
        ("geometria_plana", ["triângulo", "círculo", "área", "perímetro", "ângulo", "polígono"]),
        ("geometria_espacial", ["cubo", "esfera", "cilindro", "prisma", "pirâmide", "volume"]),
        ("geometria_analitica", ["reta", "plano cartesiano", "distância", "coordenadas"]),
        ("trigonometria", ["seno", "cosseno", "tangente", "trigonometria", "radianos"]),
        ("probabilidade", ["probabilidade", "evento", "chance", "aleatorio"]),
        ("estatistica", ["média", "mediana", "moda", "desvio", "gráfico", "tabela"]),
        ("progressoes", ["pa", "pg", "progressão", "aritmética", "geométrica"]),
        ("analise_combinatoria", ["combinação", "permutação", "arranjo", "fatorial"]),
        ("matrizes", ["matriz", "determinante", "sistema linear"]),
        ("numeros", ["número", "inteiro", "racional", "irracional", "complexo"]),
        ("porcentagem", ["porcentagem", "juros", "desconto", "acréscimo"]),
        ("razao_proporcao", ["razão", "proporção", "regra de três", "escala"]),
    ],
}


# ============== FUNÇÕES DE CLASSIFICAÇÃO ==============

def detect_language(text: str) -> str:
    """Detecta se o texto está em inglês, espanhol ou português."""
    text_lower = text.lower()
    words = re.findall(r'\b[a-záéíóúàèìòùâêîôûãõñ]+\b', text_lower)
    
    if len(words) < 10:
        return "portugues"
    
    # Palavras comuns em inglês
    english_words = {"the", "a", "an", "is", "are", "was", "were", "has", "have", "had", 
                     "will", "would", "could", "should", "can", "may", "might", "must",
                     "to", "of", "in", "on", "at", "for", "with", "by", "from", "as",
                     "that", "this", "these", "those", "it", "its", "they", "their",
                     "and", "or", "but", "not", "no", "yes", "all", "some", "any",
                     "be", "been", "being", "do", "does", "did", "done", "doing"}
    
    # Palavras comuns em espanhol (não existem em português)
    spanish_words = {"el", "los", "una", "uno", "unos", "unas", "y", "pero", "porque",
                     "está", "están", "fue", "fueron", "ser", "estar", "muy", "también",
                     "qué", "cómo", "cuál", "dónde", "cuándo", "siempre", "nunca",
                     "todo", "todos", "toda", "todas", "algo", "alguien", "nada", "nadie"}
    
    english_count = sum(1 for w in words if w in english_words)
    spanish_count = sum(1 for w in words if w in spanish_words)
    
    english_ratio = english_count / len(words)
    spanish_ratio = spanish_count / len(words)
    
    if english_ratio > 0.15:
        return "ingles"
    elif spanish_ratio > 0.08:
        return "espanhol"
    else:
        return "portugues"


def classify_by_number_and_day(numero: int, dia: int, ano: int) -> Optional[str]:
    """
    Classifica a matéria baseado no número da questão e dia da prova.
    
    Estrutura padrão do ENEM (pode variar ligeiramente):
    - Dia 1: 
      - Questões 1-5: Língua Estrangeira (Inglês ou Espanhol)
      - Questões 6-45: Português/Linguagens
      - Questões 46-90: Ciências Humanas (História, Geografia, Filosofia, Sociologia)
    - Dia 2:
      - Questões 91-135: Ciências da Natureza (Química, Física, Biologia)
      - Questões 136-180: Matemática
    """
    if dia == 1:
        if 1 <= numero <= 5:
            return "lingua_estrangeira"  # Será refinado depois
        elif 6 <= numero <= 45:
            return "portugues"
        elif 46 <= numero <= 90:
            return "humanas"  # Será refinado depois
    elif dia == 2:
        if 91 <= numero <= 135:
            return "natureza"  # Será refinado depois
        elif 136 <= numero <= 180:
            return "matematica"
    
    return None


def find_topic(text: str, materia: str) -> Optional[str]:
    """Encontra o tópico mais provável baseado em palavras-chave."""
    if materia not in TOPICOS:
        return None
    
    text_lower = text.lower()
    
    best_topic = None
    best_score = 0
    
    for topic_name, keywords in TOPICOS[materia]:
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_topic = topic_name
    
    return best_topic if best_score > 0 else None


def classify_humanas(text: str) -> str:
    """Classifica entre História, Geografia, Filosofia e Sociologia."""
    text_lower = text.lower()
    
    # Palavras-chave para cada área
    historia_kw = ["século", "guerra", "revolução", "império", "colonial", "rei", "rainha", 
                   "independência", "república", "ditadura", "escravidão", "abolição",
                   "período", "era", "antiga", "medieval", "moderna", "contemporânea",
                   "civilização", "invasão", "conquista", "tratado"]
    
    geografia_kw = ["clima", "relevo", "vegetação", "bioma", "rio", "bacia", "região",
                    "território", "país", "população", "urbano", "rural", "migração",
                    "mapa", "cartografia", "latitude", "longitude", "fronteira",
                    "agrário", "industrial", "globalização", "ambiental"]
    
    filosofia_kw = ["filósofo", "filosofia", "ética", "moral", "razão", "pensamento",
                    "sócrates", "platão", "aristóteles", "descartes", "kant", "nietzsche",
                    "metafísica", "epistemologia", "lógica", "existência"]
    
    sociologia_kw = ["sociedade", "social", "sociologia", "durkheim", "weber", "marx",
                     "classe", "capitalismo", "ideologia", "cultura", "identidade",
                     "movimento social", "desigualdade", "trabalho"]
    
    scores = {
        "historia": sum(1 for kw in historia_kw if kw in text_lower),
        "geografia": sum(1 for kw in geografia_kw if kw in text_lower),
        "filosofia_sociologia": sum(1 for kw in filosofia_kw + sociologia_kw if kw in text_lower),
    }
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "historia"


def classify_natureza(text: str) -> str:
    """Classifica entre Química, Física e Biologia."""
    text_lower = text.lower()
    
    quimica_kw = ["molécula", "átomo", "elemento", "composto", "reação", "ácido", "base",
                  "ph", "solução", "concentração", "mol", "massa molar", "ligação química",
                  "orgânico", "inorgânico", "carbono", "oxigênio", "hidrogênio",
                  "oxidação", "redução", "eletroquímica", "polímero"]
    
    fisica_kw = ["força", "movimento", "velocidade", "aceleração", "energia", "potência",
                 "trabalho", "newton", "joule", "watt", "elétrico", "magnético",
                 "onda", "frequência", "óptica", "calor", "temperatura", "pressão",
                 "circuito", "resistência", "tensão", "corrente"]
    
    biologia_kw = ["célula", "organismo", "espécie", "gene", "dna", "evolução",
                   "ecossistema", "cadeia alimentar", "fotossíntese", "respiração",
                   "digestão", "sangue", "coração", "bactéria", "vírus", "doença",
                   "planta", "animal", "proteína", "enzima", "hormônio"]
    
    scores = {
        "quimica": sum(1 for kw in quimica_kw if kw in text_lower),
        "fisica": sum(1 for kw in fisica_kw if kw in text_lower),
        "biologia": sum(1 for kw in biologia_kw if kw in text_lower),
    }
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "biologia"


def classify_question(question: dict) -> dict:
    """Classifica uma questão por matéria e tópico."""
    enunciado = question.get("enunciado", "")
    alternativas_text = " ".join([a.get("texto", "") for a in question.get("alternativas", [])])
    full_text = enunciado + " " + alternativas_text
    
    numero = question.get("numero_questao", 0)
    prova = question.get("prova", "")
    
    # Extrair dia da prova
    dia_match = re.search(r'Dia (\d)', prova)
    dia = int(dia_match.group(1)) if dia_match else 1
    
    ano = question.get("ano", 2020)
    
    # Primeira classificação por número/dia
    materia_base = classify_by_number_and_day(numero, dia, ano)
    
    # Refinar classificação
    if materia_base == "lingua_estrangeira":
        materia = detect_language(enunciado)
    elif materia_base == "humanas":
        materia = classify_humanas(full_text)
    elif materia_base == "natureza":
        materia = classify_natureza(full_text)
    elif materia_base == "portugues":
        materia = "portugues"
    elif materia_base == "matematica":
        materia = "matematica"
    else:
        # Fallback: tentar detectar pelo conteúdo
        lang = detect_language(enunciado)
        if lang in ["ingles", "espanhol"]:
            materia = lang
        else:
            materia = "portugues"
    
    # Encontrar tópico
    topico = find_topic(full_text, materia)
    
    # Atualizar questão
    question["materia"] = materia
    question["topico"] = topico
    
    return question


def process_all_questions(input_file: str, output_file: str):
    """Processa todas as questões e classifica por matéria e tópico."""
    
    print("=" * 60)
    print("CLASSIFICADOR DE QUESTÕES ENEM")
    print("=" * 60)
    
    # Carregar questões
    with open(input_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"Total de questões: {len(questions)}")
    print()
    
    # Classificar cada questão
    for i, question in enumerate(questions):
        classify_question(question)
        if (i + 1) % 200 == 0:
            print(f"  Processadas: {i + 1}/{len(questions)}")
    
    print(f"  Processadas: {len(questions)}/{len(questions)}")
    print()
    
    # Estatísticas
    by_materia = {}
    by_topico = {}
    
    for q in questions:
        materia = q.get("materia", "desconhecida")
        topico = q.get("topico", "sem_topico")
        
        by_materia[materia] = by_materia.get(materia, 0) + 1
        
        key = f"{materia}/{topico}"
        by_topico[key] = by_topico.get(key, 0) + 1
    
    print("=" * 60)
    print("ESTATÍSTICAS POR MATÉRIA")
    print("=" * 60)
    for materia in sorted(by_materia.keys()):
        print(f"  {materia}: {by_materia[materia]} questões")
    
    print()
    print("=" * 60)
    print("ESTATÍSTICAS POR TÓPICO (top 30)")
    print("=" * 60)
    sorted_topicos = sorted(by_topico.items(), key=lambda x: -x[1])[:30]
    for topico, count in sorted_topicos:
        print(f"  {topico}: {count}")
    
    # Salvar
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ Arquivo salvo: {output_file}")


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    input_file = data_dir / "questions_processed.json"
    output_file = data_dir / "questions_classified.json"
    
    process_all_questions(str(input_file), str(output_file))


if __name__ == "__main__":
    main()
