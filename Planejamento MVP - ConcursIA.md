  
**UNIVERSIDADE FEDERAL DE CAMPINA GRANDE**  
**CENTRO DE ENGENHARIA ELÉTRICA E INFORMÁTICA**  
**UNIDADE ACADÊMICA DE SISTEMAS EM COMPUTAÇÃO**  
**PROJETO EM COMPUTAÇÃO I**  
**DOCENTE: CARLOS EDUARDO SANTOS PIRES**

ANDREZA VILAR DE FARIAS — 121210930  
ARTHUR ANTUNES PINTO DANTAS SILVA  —121110966  
GABRIEL SANTOS ALVES  — 121210581  
GUILHERME ALBERTO DUTRA CAMELO  — 121210159  
JOSÉ ARTUR PROCOPIO COELHO  — 120210625

**ConcursIA**

1. # **Definição do tema**

   1. ## **Objetivo do projeto**

Partindo do conceito inicial de um assistente RAG para o ENEM (visto no repositório enem\_rag\_assistant), o objetivo deste projeto é expandir essa ideia para um ecossistema de preparação completo. O objetivo não é ser apenas um "tira-dúvidas", mas uma plataforma robusta que justifique o valor para usuários (alunos) e clientes B2B (cursinhos), focando em retenção, performance e produtividade. O sistema irá evoluir de um assistente focado no ENEM para uma plataforma multi-concurso (incluindo OAB, TRFs, etc.), servindo diferentes personas (Aluno, Professor, Gestor de Cursinho).

2. ## **Módulos da Plataforma (Visão de Produto)**

    A plataforma será dividida nos seguintes módulos principais:

* **Módulo 1: O Aluno (Foco em Performance e Planejamento)**  
  * **Plano de Estudos Dinâmico:** IA que monta e auto ajusta cronogramas com base em metas, tempo disponível e análise de erros (RAG).  
  * **Simulados e Listas "On-Demand":** Geração de listas de exercícios e simulados personalizados (ex: "10 questões da banca FGV dos últimos 3 anos").  
  * **Dashboard de Performance:** Analytics pessoal com taxa de acerto por tópico, matéria e comparação com notas de corte.  
  * **"Dissecador de Editais":** Ferramenta de RAG para "traduzir" editais, extraindo datas, requisitos e tópicos mais relevantes.  
* **Módulo 2: O Professor (Foco em Produtividade e Criação)**  
  * **Montador de Aulas e Materiais:** IA que sugere estruturas de aula, busca questões de provas passadas e propõe "ganchos" para tópicos específicos.  
  * **Gerador de Provas (com Gabarito Comentado):** Ferramenta robusta para criar provas, selecionar de um banco ou gerar novas questões no estilo da banca, incluindo rascunhos de comentários para o gabarito.  
  * **Banco de Questões Inteligente:** Todas as questões indexadas com tags avançadas (matéria, tópico, ano, banca, dificuldade).  
* **Módulo 3: O Gestor do Cursinho (Foco em Admin e Analytics)**  
  * **Dashboard de Gestão de Turmas:** Visão geral do desempenho de turmas, identificando gargalos de aprendizado.  
  * **Gestão de Conteúdo Próprio (White-Label):** Permite que o cursinho faça upload de suas próprias apostilas, que passam a ser indexadas pelo RAG daquele cliente.  
  * **Gestão de Usuários:** Painel para gerenciar acessos de professores e alunos.  
* **Módulo 4: "O Radar" (Módulo de Prospecção)**  
  * **Radar de Editais:** Monitoramento ativo (via scraping/APIs) de concursos abertos, previstos e em andamento, com filtros avançados.  
  * **Notificador de Concursos:** Alertas por e-mail para usuários com base em perfis de interesse salvos.

  3. #### **Critérios de Aceitação (Escopo do MVP \- Fase 1\)**

Para a entrega deste projeto (MVP), o foco será em **1 concurso (ENEM)** e **2 personas (Aluno e Professor)**, validando as funcionalidades centrais.

* **Backend:** Sistema de autenticação (Login/Cadastro) funcional.  
* **Backend:** Pipeline de ingestão de dados (ETL) para PDFs (editais e provas do ENEM) está funcional.  
* **Backend:** Arquitetura RAG (Banco Vetorial \+ Orquestrador) configurada e respondendo a consultas.  
* **Módulo Aluno (MVP):** O "Chatbot Especialista" (RAG puro) está funcional, respondendo perguntas sobre o edital do ENEM.  
* **Módulo Aluno (MVP):** O "Gerador de Simulados On-Demand" (versão simples) está funcional, permitindo gerar uma lista de exercícios baseada em filtros simples.  
* **Módulo Professor (MVP):** O "Banco de Questões Inteligente" (versão simples) permite buscar e filtrar questões do ENEM.  
* **Validação:** A acurácia do RAG (respostas baseadas nos editais) é considerada aceitável em testes manuais.

  4. #### **Entregas do projeto**

* Descrição do MVP com as funcionalidades do sistema (este documento).  
* Design das telas da aplicação  
* Desenvolvimento da aplicação (código-fonte do MVP \- Fase 1).  
* Testes unitários, de integração e de usabilidade.  
* Implantação do sistema (demonstração funcional).

  5. #### **Experiência do Usuário**

O design da interface será focado na clareza e eficiência. A plataforma deve se adaptar à persona logada (Aluno, Professor, Gestor), apresentando "Hubs" distintos (ex: "Hub do ENEM", "Hub da OAB") para personalizar a jornada e evitar sobrecarga de informação. A navegação deve ser fluida, permitindo ao aluno focar nos estudos e ao professor focar na criação de conteúdo.

**2\. Equipe vs Papéis Iniciais**  
No projeto, teremos alguns papéis principais desempenhados pelos integrantes do grupo: **Product Owner (PO)**, **Scrum Master (SM)**, **Desenvolvedor Frontend** e **Desenvolvedor Backend**. Cada função possui atribuições específicas para garantir o sucesso na entrega do MVP.

* **Product Owner:** É responsável pela definição do escopo do projeto, pela análise e priorização dos requisitos e pela validação das entregas.  
* **Scrum Master:** Atua como facilitador da equipe, garantindo que o projeto avance de acordo com os prazos e promovendo uma distribuição equilibrada das tarefas.  
* **Desenvolvedor:** É responsável pela criação e implementação do código. Dentro desse papel, os desenvolvedores podem assumir diferentes frentes:  
  * **Frontend:** Desenvolvimento da interface web (React/Vue), garantindo a experiência de usuário fluida para as diferentes personas.  
  * **Backend:** Implementação das lógicas de negócio (Python/FastAPI), APIs, autenticação e o pipeline RAG.  
  * **Banco de Dados (SQL):** Modelagem e gerenciamento do banco relacional (PostgreSQL) para dados estruturados (usuários, questões, métricas).  
  * **Banco de Dados (Vetor):** Configuração e gerenciamento do Vector DB (ChromaDB/Pinecone) para a busca semântica.  
  * **Testes:** Planejamento e execução de testes (funcionais, usabilidade e acurácia do RAG).

| Membro | Papel Desempenhado |
| :---- | :---- |
| Andreza Vilar de Farias | Desenvolvedora Backend |
| Arthur Antunes Pinto Dantas Silva | Scrum Master e Desenvolver Backend |
| Gabriel Santos Alves | Desenvolvedor Frontend |
| Guilherme Alberto Dutra Camelo | Product Owner e Desenvolvedor Backend |
| José Artur Procopio Coelho | Desenvolvedor Frontend |

# **3\. Plano de Projeto (Roadmap da Plataforma)**

## **Fase 1: Concepção e Arquitetura** 

* **Definição de Escopo do MVP:** Focar em 1 concurso (ENEM) e 2 personas (Aluno Independente e Professor).  
* **Mapeamento da Jornada do Usuário:** Desenhar fluxos de cadastro, geração de simulado (aluno) e criação de lista (professor).  
* **Definição da Arquitetura de Tecnologia:**  
  * **Frontend:** React.  
  * **Backend:** Python/FastAPI (preferencial) ou Node.js/Express.  
  * **Banco de Dados (Questões):** PostgreSQL para dados estruturados (questões, usuários, métricas).  
* **Definição da Arquitetura RAG:**  
  * **Ingestão de Dados (ETL):** Pipeline para processar PDFs (editais, provas), aplicar *chunking* e limpeza.  
  * **Banco Vetorial (Vector DB):** ChromaDB (para MVP local) ou Pinecone/Weaviate (para produção).  
  * **Orquestrador (LLM):** LangChain ou LlamaIndex.  
  * **Modelo de LLM:** API do Google Gemini ou OpenAI GPT-4.  
* **Coleta de Dados Inicial (Corpus):** Coletar e organizar os 10 últimos editais e provas do ENEM.

  ## **Fase 2: Desenvolvimento do MVP** 

* **Backend (Core):**  
  * Construir o sistema de autenticação (Login/Cadastro).  
  * Desenvolver o pipeline de ingestão de dados (ETL).  
  * Configurar o Banco Vetorial e o RAG.  
* **Frontend (Módulos MVP):**  
  * **Módulo Aluno:** O "Chatbot Especialista" (RAG puro) e o "Gerador de Simulados On-Demand" (simples).  
  * **Módulo Professor:** O "Banco de Questões Inteligente" (apenas busca e filtro).  
* **Testes e Validação:**  
  * Testar a acurácia do RAG (respostas corretas baseadas nos editais).  
* **Meta do MVP:** Lançar para um pequeno grupo de alunos/professores (beta fechado) para validar a utilidade do RAG e do gerador de simulados.

# **4\. Cronograma** 

| Sprint | Data | Iterações | Descrição |
| :---- | :---- | :---- | :---- |
| 0 | 05/11/2025 | Reunião | Reunião para finalização do documento inicial (este) |
| 0 | 07/11/2025 | Entrega | Submissão do documento da Entrega Parcial 1 |
| 1 | 10/11/2025 | Reunião | Alinhamento da equipe e definição da Sprint 1 (Fase 0: Arquitetura, Coleta de Dados, Auth) |
| 1 | 12/11/2025 | Acompanhamento | Discussão de bloqueios e sugestões |
| 2 | 14/11/2025 | Reunião | Definição da Sprint 2 (Fase 1: Backend Core, Pipeline ETL, RAG básico) |
| 2 | 19/11/2025 | Acompanhamento | Discussão de bloqueios e sugestões |
| 3 | 24/11/2025 | Reunião | Definição da Sprint 3 (Fase 1: Frontend Módulos Aluno e Professor, Testes de acurácia) |
| 3 | 28/11/2025 | Acompanhamento | Discussão de bloqueios e sugestões |
| 3 | 03/12/2025 | Reunião | Reunião interna de alinhamento da equipe |
| 3 | 06/12/2025 | Reunião | Reunião interna de alinhamento da equipe |
| 3 | 10/12/2025 | Acompanhamento | Discussão de bloqueios e sugestões |
| 3 | 12/12/2025 | Reunião | Reunião interna de alinhamento da equipe |
| 3 | 19/12/2025 | Reunião | Reunião interna de alinhamento da equipe |
| 3 | 17/12/2025 | Acompanhamento | Discussão de bloqueios e sugestões |
| 4 | 19/01/2026 | Reunião | Definição da Sprint 4 (Incorporar feedback, refatoração, testes finais de usabilidade) |
| 4 | 26/01/2026 | Acompanhamento | Discussão de bloqueios e sugestões |
| 4 | 02/02/2026 | Reunião | Reunião interna de alinhamento da equipe |
| 4 | 04/02/2026 | Acompanhamento | Discussão de bloqueios e sugestões |
| 4 | 09/02/2026 | Reunião | Reunião interna de alinhamento da equipe |
| 4 | 11/02/2026 | Acompanhamento | Discussão de bloqueios e sugestões |
| 4 | 23/02/2026 | Reunião | Reunião interna de alinhamento da equipe |
| 4 | 25/02/2026 | Acompanhamento | Discussão de bloqueios e sugestões |
| 4 | 27/02/2026 | Reunião | Finalização e revisão final do MVP para a Entrega Parcial do MVP com ajustes |
| 4 | 06/03/2026 | Reunião | Entrega final |
| 4 | 11/03/2026 | Apresentação | Apresentação do projeto |

# **5\. Arquitetura e Principais Tecnologias**

## **5.1. Frontend (Aplicativo Web)**

* **Tecnologia:** React  
* **Descrição:** O frontend será desenvolvido como uma Single Page Application (SPA), responsável pela interface do usuário, consumo de APIs RESTful e pela experiência de navegação adaptativa para os diferentes tipos de usuários, tais como aluno e professor.

  ## **5.2. Backend (Servidor e Apis)**

* **Tecnologias:** Python com FastAPI.  
* **Descrição:** O backend será desenvolvido com FastAPI, responsável por toda a lógica de negócio, controle de autenticação, gerenciamento dos dados estruturados e exposição de APIs RESTful para o frontend e para o orquestrador RAG. 

  ## **5.3. Banco de dados**

* **Tecnologia:** PostgreSQL.  
* **Descrição:** O PostgreSQL foi escolhido por sua robustez. Ele será responsável pelo armazenamento estruturado dos dados do sistema (usuários, perfis, questões, métricas de desempenho, turmas, etc.)

  ## **5.4. Arquitetura RAG (Inteligência)**

* **Ingestão de Dados (ETL):** Um pipeline (script Python) responsável por receber PDFs (edital, prova, apostila), aplicar chunking (divisão inteligente de texto) e limpeza.  
* **Banco de Dados Vetorial (Vector DB):**  
* **Tecnologia:** Chroma DB.  
* **Descrição:** Armazena os embeddings (vetores) dos chunks de documentos para permitir a busca semântica de alta velocidade.  
* **Orquestrador (LLM):**  
* **Tecnologia:** LangChain.  
* **Descrição:** O "cérebro" que conecta a pergunta do usuário, a busca no Chroma DB (para obter contexto) e faz geração da resposta final.  
* **Modelo de Linguagem (LLM):**  
  * **Tecnologia:** API do Google Gemini  
  * **Descrição:** O modelo de linguagem que vai efetivamente gerar as respostas em linguagem natural, com base no contexto fornecido pelo RAG.

	  
**6\. Testes Críticos**

## **6.1 Testes de funcionalidade**

| Teste | Descrição |
| :---- | :---- |
| Teste de Acurácia do RAG | **(Mais Crítico)** Garante que perguntas factuais (ex: "Qual a data da prova?") retornam a informação correta baseada nos editais indexados. |
| Teste de Resposta "Não Sei" | Garante que o sistema responde que não sabe se a pergunta for sobre algo fora dos documentos indexados (evitando "alucinação"). |
| Teste de Geração de Simulado | Verifica se o "Gerador On-Demand" (MVP) cria uma lista de questões que corresponde aos filtros (ex: matéria, ano). |
| Teste de Ingestão de Documento | Garante que um novo PDF (edital) pode ser carregado, processado e vetorizado, ficando disponível para consulta pelo RAG. |
| Teste de Autenticação de Persona | Verifica se o login de Aluno, Professor e Gestor (quando implementado) direciona para dashboards distintos. |
| Teste de Busca de Questões | Garante que o "Banco de Questões Inteligente" (MVP) filtra e retorna as questões corretas. |

## **6.2. Testes de Usabilidade**

| Teste | Descrição |
| :---- | :---- |
| Teste de Primeira Experiência | Avalia se novos usuários (Aluno, Professor) entendem como usar suas ferramentas principais (Chatbot, Gerador de Simulado). |
| Teste de Feedback Visual | Garante que ações (gerar simulado, perguntar ao RAG) retornem mensagens claras de sucesso, carregamento ou erro. |
| Teste de Navegação nos Hubs | Verifica se a separação por "Hubs" (ENEM, OAB) é intuitiva e clara. |
| Teste de Responsividade | Testa a interface em diferentes dispositivos (desktop, tablet, celular). |

## **6.3. Testes de Desempenho**

| Teste | Descrição |
| :---- | :---- |
| Teste de Carga (Simples) | Mede o desempenho com múltiplos usuários (ex: 10\) fazendo perguntas ao RAG e gerando simulados ao mesmo tempo. |
| Teste de Tempo de Resposta (RAG) | Verifica a velocidade de ponta a ponta (pergunta do usuário \-\> resposta na tela), incluindo busca vetorial e geração do LLM. |
| Teste de Tempo de Ingestão | Avalia a performance e o tempo necessário para processar e indexar um edital completo. |

## **6.4. Teste de Integração**

| Teste | Descrição |
| :---- | :---- |
| Teste Frontend-Backend | Verifica se as ações no frontend (ex: login, gerar simulado) refletem corretamente no backend (FastAPI) e são salvas no PostgreSQL. |
| Teste Backend-RAG | Garante que a API do backend consegue se comunicar com o orquestrador (LangChain), realizar a busca no VectorDB e chamar o LLM. |

# **7\. Ambiente de Integração**

* ### **Gerenciamento do Projeto:** A gestão e organização do projeto serão realizadas através do GitHub, utilizando recursos como Projects, Issues e Milestones. A equipe utilizará a abordagem de Kanban.

* ### **Versionamento de Código:** Todo o controle de versão será feito por meio do Git, com repositório central hospedado no GitHub. Serão adotadas boas práticas como branches temáticas, pull requests e commits semânticos.

* ### **Desenvolvimento Local:** Cada desenvolvedor irá trabalhar localmente. O projeto contará com um arquivo README contendo instruções de configuração (dependências, variáveis de ambiente, inicialização dos bancos de dados).

* ### **Comunicação da Equipe:** Será utilizado o um servidor Discord para comunicação ágil, documentando o processo de desenvolvimento e de reuniões.

# **8\. Riscos**

| Classificação de Risco | Impacto e Descrição do Risco | Estratégia de Diminuição e/ou Plano de Contingência |
| :---: | :---: | :---: |
| Alto  | Atrasos nas entregas devido à complexidade subestimada das atividades (ex: pipeline de ingestão de dados). | Procurar estabelecer atividades bem definidas, prazos claros e realistas, e acompanhamento contínuo com reuniões semanais.   |
| Alto | Dificuldades de comunicação entre os membros da equipe devido a ausência de expressividade, resultando em mal-entendidos e retrabalho. | Estabelecimento de canais de comunicação claros e regulares. Utilizar técnicas de análise de postura para identificar necessidades não comunicadas de membros da equipe. |
| Médio | Dificuldade de integração e entendimento das ferramentas (LangChain, Vector DBs, FastAPI). | Avaliar e testar todas as ferramentas no início do projeto. Utilizar provas de conceitos. Sob prováveis inadequações, pesquisar alternativas e alterar abordagem para desenvolvimento.  |
| Alto | Mudanças significativas nos requisitos ao longo do projeto, afetando o escopo e o desenvolvimento (Scope Creep). | Submeter entregáveis realizados por iteração e feedback de cliente, seguindo os princípios do Scrum, para lidar com mudanças de requisitos. Checar continuamente a satisfação dos stakeholders para evitar mudanças muito bruscas.  |
| Alto  | Baixa produtividade ou falhas na entrega de tarefas devido à falta de comprometimento dos desenvolvedores.  | Definir metas claras, acompanhar regularmente o progresso e criar um ambiente motivador e colaborativo.  |
| Alto  | Acesso limitado a recursos técnicos, dificultando o desenvolvimento. | Garantir acesso às ferramentas necessárias e buscar suporte da universidade para fornecer recursos adequados.  |
| Alto  | Desistência ou ausência de membros da equipe. | Preparar backups de tarefas e documentar todos os processos e código, reorganizando as divisões das atividades.  |
| Alto | O volume de trabalho excede a capacidade da equipe, resultando em sobrecarga. | Divisão equilibrada de tarefas e monitoramento da carga de trabalho.  |
| Médio | Falta de experiência dos desenvolvedores com tecnologias ou metodologias. | Realizar mentorias e treinamentos iniciais (pair programming) para familiarizar os desenvolvedores com as tecnologias e práticas.  |
| Médio | Dificuldades na Gestão de Tempo. | Estabelecer um cronograma flexível que integre todas as responsabilidades acadêmicas e utilizar ferramentas de colaboração online para trabalho remoto.  |
| Médio | Variação na motivação dos alunos ao longo do projeto, impactando a qualidade do trabalho. | Realizar reuniões de feedback e promover um ambiente de apoio, reconhecendo o esforço dos desenvolvedores.   |
| Médio | Excesso de confiança e liderança, prometendo uma produtividade inatingível na realidade.  | Acompanhar semanalmente a realização de atividades e distribuição de tarefas, evitando desequilíbrio e excesso de responsabilidades para poucas pessoas. Dosar a estimativa de tempo com o trabalho a ser feito por cada desenvolvedor. |
| **Alto (Técnico)** | **"Alucinação" do LLM ou Acurácia do RAG.** O RAG pode falhar em encontrar o contexto correto, ou o LLM pode ignorar o contexto e gerar informação falsa, minando a confiança na plataforma. | Melhoria contínua dos *prompts* (prompt engineering). Ajuste dos parâmetros de busca (*chunk size*, *overlap*). Curadoria rigorosa dos documentos de entrada. Implementar RAG-Ops para monitoramento. |

