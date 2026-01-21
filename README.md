# ConcursIA Backend

Backend da plataforma ConcursIA - Assistente de estudos com RAG para preparação de concursos.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- Docker e Docker Compose
- Git

### Configuração

1. **Clone o repositório e acesse o diretório:**
   ```bash
   cd Backend
   ```

2. **Copie o arquivo de variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```

3. **Inicie o banco de dados PostgreSQL:**
   ```bash
   docker compose up -d db
   ```

4. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou: venv\Scripts\activate  # Windows
   ```

5. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Execute as migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Inicie o servidor de desenvolvimento:**
   ```bash
   uvicorn src.main:app --reload
   ```

8. **Acesse a documentação da API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Estrutura do Projeto

```
Backend/
├── src/
│   ├── api/              # Rotas e endpoints
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py
│   │       │   ├── questions.py
│   │       │   ├── simulados.py
│   │       │   └── chat.py
│   │       └── router.py
│   ├── config/           # Configurações
│   │   ├── database.py
│   │   └── settings.py
│   ├── models/           # Models SQLAlchemy
│   │   ├── user.py
│   │   ├── question.py
│   │   └── simulado.py
│   ├── schemas/          # Schemas Pydantic
│   ├── services/         # Lógica de negócio
│   └── main.py           # Entrada da aplicação
├── alembic/              # Migrations
├── Chatbot/              # Submódulo RAG (existente)
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🛠️ Comandos Úteis

### Banco de Dados
```bash
# Criar nova migration
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

### Docker
```bash
# Subir apenas o banco
docker compose up -d db

# Subir toda a stack (banco + API)
docker compose up -d

# Ver logs
docker compose logs -f

# Parar tudo
docker compose down
```

## 📝 Roadmap (MVP)

- [x] **Fase 0:** Fundação (FastAPI + PostgreSQL + Alembic)
- [ ] **Fase 1:** Banco de Questões (CRUD + Filtros)
- [ ] **Fase 2:** Gerador de Simulados
- [ ] **Fase 3:** Integração RAG (Chatbot)
- [ ] **Fase 4:** Usuários Simplificado

## 📚 Documentação

Consulte o arquivo `Planejamento MVP - ConcursIA.md` para detalhes completos do projeto.