#!/bin/bash

# Script de inicialização do ConcursIA Backend
# Este script configura o ambiente e inicia o banco de dados

set -e

echo "🚀 Iniciando setup do ConcursIA Backend..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar Docker
echo "1️⃣  Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker não está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker encontrado${NC}"

# 2. Iniciar PostgreSQL com Docker Compose
echo ""
echo "2️⃣  Iniciando PostgreSQL..."
docker-compose up -d db
echo -e "${GREEN}✓ PostgreSQL iniciado${NC}"

# 3. Aguardar PostgreSQL estar pronto
echo ""
echo "3️⃣  Aguardando PostgreSQL ficar pronto..."
sleep 5
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T db pg_isready -U concursia -d concursia_db >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL está pronto${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Tentativa $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ PostgreSQL não respondeu em tempo hábil${NC}"
    exit 1
fi

# 4. Instalar dependências Python
echo ""
echo "4️⃣  Instalando dependências Python..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependências instaladas${NC}"

# 5. Inicializar banco de dados
echo ""
echo "5️⃣  Inicializando tabelas do banco..."
python -c "
import sys
sys.path.insert(0, '.')
from src.core.startup import init_db, check_database_health
try:
    init_db()
    health = check_database_health()
    if health['status'] == 'healthy':
        print('✓ Banco de dados inicializado com sucesso')
    else:
        print('⚠ Banco inicializado mas com aviso: ' + str(health['error']))
except Exception as e:
    print(f'✗ Erro ao inicializar: {e}')
    sys.exit(1)
"
echo -e "${GREEN}✓ Banco de dados pronto${NC}"

echo ""
echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
echo ""
echo "Para iniciar a API, execute:"
echo "  python src/main.py"
echo ""
echo "Ou com uvicorn diretamente:"
echo "  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
