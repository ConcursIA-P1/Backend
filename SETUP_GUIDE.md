# 🚀 Guia de Inicialização - ConcursIA Backend

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.9+
- pip

## 🔧 Setup Rápido (Recomendado)

Execute o script de inicialização automática:

```bash
cd Backend
bash scripts/init_setup.sh
```

Este script irá:

1. ✓ Verificar Docker
2. ✓ Iniciar PostgreSQL
3. ✓ Instalar dependências Python
4. ✓ Inicializar tabelas do banco de dados
5. ✓ Exibir instruções para iniciar a API

## 📝 Setup Manual

Se preferir fazer passo a passo:

### 1. Iniciar o PostgreSQL

```bash
cd Backend
docker-compose up -d db
```

Verificar se está pronto:

```bash
docker-compose logs db
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Inicializar Banco de Dados

```bash
python -c "
from src.core.startup import init_db
init_db()
"
```

### 4. Iniciar a API

```bash
# Opção 1: Via Python
python src/main.py

# Opção 2: Via Uvicorn (com reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Opção 3: Via Docker Compose
docker-compose up api
```

## ✅ Verificação

### Testar Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Resposta esperada:

```json
{
  "status": "ok",
  "app_name": "ConcursIA API",
  "version": "0.1.0",
  "database": "healthy"
}
```

### Testar Documentação

- Acesse: http://localhost:8000/docs
- Ou: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Erro de Conexão com o Banco

**Problema**: `Error: CORS header 'Access-Control-Allow-Origin' missing. Status code: 500`

**Solução**:

1. Verifique se o PostgreSQL está rodando:

   ```bash
   docker-compose ps
   ```

2. Se não estiver, inicie:

   ```bash
   docker-compose up -d db
   ```

3. Reinicie a API

### ModuleNotFoundError: No module named 'sqlalchemy'

**Solução**: Instale as dependências

```bash
pip install -r requirements.txt
```

### Tabelas não Existem

A aplicação cria automaticamente as tabelas na inicialização. Se ainda tiver problemas:

```bash
python -c "from src.core.startup import init_db; init_db()"
```

### Limpar e Reiniciar (Reset Completo)

```bash
# Parar containers
docker-compose down

# Remover volume do PostgreSQL (CUIDADO: Apaga dados!)
docker-compose down -v

# Reiniciar tudo
bash scripts/init_setup.sh
```

## 📚 Estrutura da API

- **Health Check**: `GET /api/v1/health`
- **Simulados**:
  - `GET /api/v1/simulados` - Lista simulados
  - `POST /api/v1/simulados/generate` - Gera simulado customizado
  - `POST /api/v1/simulados/quick` - Gera simulado rápido
  - `GET /api/v1/simulados/{id}` - Busca simulado específico

## 🔗 Frontend Integration

Quando tudo estiver funcionando, o frontend em `localhost:3000` conseguirá acessar:

```
http://localhost:8000/api/v1
```

CORS está habilitado para todas as origens em desenvolvimento.

## 📞 Suporte

Para mais informações, consulte:

- [Backend README](./README.md)
- Documentação Swagger: http://localhost:8000/docs
