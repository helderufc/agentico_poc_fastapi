# PoC LLM UFC

Plataforma LMS (Learning Management System) desenvolvida para a UFC, inspirada na Anthropic Academy. Backend API REST em FastAPI com IA embarcada para geração de conteúdo de aulas e quizzes de módulos.

## Stack

- **Python** 3.12.3
- **FastAPI** 0.109 + Uvicorn
- **PostgreSQL** 16 + SQLAlchemy 2.0 + Alembic
- **Autenticação**: JWT (PyJWT) + bcrypt
- **IA**: OpenAI GPT-4o · Google Gemini · Groq (prioridade: Gemini > Groq > OpenAI)
- **Filas**: Redis + Celery 5.3
- **Outras**: Pydantic v2, Bleach, pypdf, Pillow

## Perfis de Usuário

| Perfil | Descrição |
|---|---|
| `ADMIN` | Pré-cadastrado; ativa/desativa contas |
| `PROFESSOR` | Cria e gerencia cursos, módulos, aulas e provas |
| `ALUNO` | Se inscreve e consome cursos (Fase 2) |

## Setup

### 1. Criar e ativar virtualenv
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar ambiente
```bash
cp .env.example .env
# Editar .env com suas credenciais
```

Variáveis obrigatórias:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do PostgreSQL |
| `SECRET_KEY` | Chave secreta para JWT |
| `REDIS_URL` | URL do Redis (padrão: `redis://localhost:6379/0`) |

Pelo menos uma chave de IA:

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Google Gemini (prioridade máxima) |
| `GROQ_API_KEY` | Groq |
| `OPENAI_API_KEY` | OpenAI GPT-4o (fallback) |

### 4. Criar banco de dados e rodar migrações
```bash
createdb llm_ufc
alembic upgrade head
```

### 5. Rodar a aplicação

São necessários **três processos** rodando em paralelo:

**Terminal 1 — Redis** (pular se já estiver rodando)
```bash
redis-server
# ou via Docker:
docker run -d -p 6379:6379 redis
```

**Terminal 2 — FastAPI**
```bash
uvicorn main:app --reload
```

**Terminal 3 — Celery worker** (obrigatório para geração de conteúdo via IA)
```bash
celery -A br.ufc.llm.shared.service.celery_app.celery_app worker --loglevel=info
```

A API estará disponível em `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Geração de Conteúdo via IA (Assíncrono)

Os endpoints de IA são **assíncronos** — retornam imediatamente um `task_id` e processam em background via Celery.

**Fluxo:**
```
1. POST /modulos/{id}/aulas/{id}/gerar-conteudo
   ← 202 { "data": { "task_id": "abc-123", "status": "processando" } }

2. GET /tasks/abc-123          (polling até concluir)
   ← 200 { "data": { "status": "concluido", "resultado": { "conteudo_gerado": "<html>..." } } }

3. POST /modulos/{id}/aulas/{id}/confirmar-conteudo
   ← 200  (persiste o conteúdo aprovado)
```

Estados possíveis da task: `pendente` · `processando` · `concluido` · `erro`

## Endpoints

### Autenticação (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/cadastro` | Cadastrar novo usuário (status inicia como INATIVO) |
| `POST` | `/auth/login` | Login e geração de tokens JWT |
| `POST` | `/auth/refresh` | Renovar access token |
| `POST` | `/auth/recuperar-senha` | Solicitar link de recuperação de senha |
| `POST` | `/auth/redefinir-senha` | Redefinir senha com token |

### Perfil (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/perfil` | Obter perfil do usuário logado |
| `PUT` | `/perfil/foto` | Upload de foto de perfil (JPG/PNG/GIF, mín. 200×200px) |
| `PUT` | `/perfil/senha` | Alterar senha |

### Admin (`/api/v1/admin`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/admin/usuarios` | Listar usuários (paginado) |
| `PATCH` | `/admin/usuarios/{id}/ativar` | Ativar conta de usuário |
| `PATCH` | `/admin/usuarios/{id}/desativar` | Desativar conta de usuário |

### Cursos (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/cursos` | Criar curso |
| `GET` | `/cursos` | Listar cursos do professor |
| `GET` | `/cursos/{id}` | Obter curso |
| `PUT` | `/cursos/{id}` | Editar curso |
| `DELETE` | `/cursos/{id}` | Deletar curso |
| `PATCH` | `/cursos/{id}/publicar` | Publicar curso |
| `PATCH` | `/cursos/{id}/arquivar` | Arquivar curso |
| `PUT` | `/cursos/{id}/capa` | Upload de capa |

### Módulos (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/cursos/{id}/modulos` | Criar módulo |
| `GET` | `/cursos/{id}/modulos` | Listar módulos |
| `GET` | `/cursos/{id}/modulos/{id}` | Obter módulo |
| `PUT` | `/cursos/{id}/modulos/{id}` | Editar módulo |
| `DELETE` | `/cursos/{id}/modulos/{id}` | Deletar módulo |
| `PUT` | `/cursos/{id}/modulos/{id}/capa` | Upload de capa |

### Aulas (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/modulos/{id}/aulas` | Criar aula |
| `GET` | `/modulos/{id}/aulas` | Listar aulas |
| `GET` | `/modulos/{id}/aulas/{id}` | Obter aula |
| `PUT` | `/modulos/{id}/aulas/{id}` | Editar aula |
| `DELETE` | `/modulos/{id}/aulas/{id}` | Deletar aula |
| `PUT` | `/modulos/{id}/aulas/{id}/arquivo` | Upload de arquivo (PDF ou vídeo) |
| `POST` | `/modulos/{id}/aulas/{id}/gerar-conteudo` | **[Async]** Gerar conteúdo via IA |
| `POST` | `/modulos/{id}/aulas/{id}/confirmar-conteudo` | Confirmar e salvar conteúdo gerado |

### Provas (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/modulos/{id}/prova` | Criar prova no módulo |
| `GET` | `/modulos/{id}/prova` | Obter prova |
| `PUT` | `/modulos/{id}/prova` | Editar prova |
| `DELETE` | `/modulos/{id}/prova` | Deletar prova |
| `POST` | `/modulos/{id}/prova/manual` | Criar quiz com perguntas manualmente |
| `POST` | `/modulos/{id}/prova/gerar-quiz-ia` | **[Async]** Gerar quiz via IA |
| `GET` | `/modulos/{id}/prova/estatisticas` | Estatísticas da prova |
| `POST` | `/provas/{id}/perguntas` | Adicionar pergunta |
| `PUT` | `/provas/{id}/perguntas/{id}` | Editar pergunta |
| `DELETE` | `/provas/{id}/perguntas/{id}` | Deletar pergunta |

### Tasks — Celery (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/tasks/{task_id}` | Consultar status e resultado de uma task assíncrona |

### Matrículas — Perfil Aluno (`/api/v1`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/catalogo/cursos` | Listar catálogo de cursos publicados |
| `GET` | `/catalogo/cursos/{id}` | Obter detalhes de curso no catálogo |
| `POST` | `/matriculas` | Matricular-se em um curso |
| `GET` | `/matriculas` | Listar minhas matrículas |
| `GET` | `/matriculas/{curso_id}/modulos` | Listar módulos do curso matriculado |
| `GET` | `/matriculas/{curso_id}/modulos/{mod_id}/aulas` | Listar aulas do módulo |
| `GET` | `/matriculas/{curso_id}/modulos/{mod_id}/aulas/{aula_id}` | Obter aula completa |
| `GET` | `/matriculas/{curso_id}/modulos/{mod_id}/prova` | Obter prova (sem gabarito) |
| `POST` | `/provas/{id}/responder` | Enviar respostas da prova |
| `GET` | `/provas/{id}/resultado` | Obter resultado da prova |

## Estrutura do Projeto

```
br/ufc/llm/
├── usuario/     # Autenticação, perfil, admin
├── curso/       # Gerenciamento de cursos
├── modulo/      # Gerenciamento de módulos
├── aula/        # Aulas + geração de conteúdo via IA
├── prova/       # Provas, perguntas e quiz via IA
├── matricula/   # Matrículas e consumo de conteúdo (aluno)
└── shared/
    ├── service/
    │   ├── celery_app.py    # Instância Celery
    │   └── openai_service.py  # Wrapper IA (OpenAI/Gemini/Groq)
    ├── tasks/
    │   └── ia_tasks.py      # Tasks assíncronas de IA
    ├── controller/
    │   └── task_controller.py  # Endpoint de polling
    └── domain/              # JWT, resposta padrão
```

Cada domínio segue a estrutura: `controller · service · repository · domain · dto · exception`

## Convenções

- **Idioma**: Português para entidades, campos, métodos e variáveis de domínio
- **DTOs**: `XxxRequest` (entrada) e `XxxResponse` (saída)
- **Resposta padrão**: `{ "data": {}, "message": "", "status": 200 }`
- **Commits**: Português imperativo — `"Adiciona endpoint de criação de curso"`
- **Testes**: TDD — escritos antes da implementação

## Testes

```bash
pytest
```

## Fases

- **Fase 1 (Concluída)**: Perfil Professor — auth, perfil, cursos, módulos, aulas, provas com IA
- **Fase 2 (Em andamento)**: Perfil Aluno — matrícula, consumo de conteúdo, realização de provas
