# PoC LLM UFC

Platform LMS (Learning Management System) desenvolvida para a UFC, com backend API REST em FastAPI com IA embarcada.

## Setup

### 1. Ativar virtualenv
```bash
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

### 4. Configurar banco de dados PostgreSQL
```bash
# Criar banco de dados
createdb llm_ufc

# Rodar migrações (quando implementadas)
alembic upgrade head
```

### 5. Rodar aplicação
```bash
python main.py
```

A API estará disponível em `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estrutura do Projeto

```
br/ufc/llm/
├── usuario/          # Gerenciamento de usuários
│   ├── controller/   # Endpoints REST
│   ├── service/      # Lógica de negócio
│   ├── repository/   # Acesso a dados
│   ├── domain/       # Entidades
│   ├── dto/          # Data Transfer Objects
│   └── exception/    # Exceções customizadas
├── curso/            # Gerenciamento de cursos
├── modulo/           # Gerenciamento de módulos
├── aula/             # Gerenciamento de aulas
├── prova/            # Gerenciamento de provas
└── shared/           # Código compartilhado
```

## Convenções

- **Idioma**: Português para nomes de entidades, campos, métodos e variáveis de domínio
- **DTOs**: `XxxRequest` (entrada) e `XxxResponse` (saída)
- **Commits**: Português imperativo (ex: "Adiciona endpoint de criação de curso")
- **Testes**: Escritos ANTES da implementação (TDD)

## Fases

- **Fase 1 (Atual)**: Perfil Professor (auth, perfil, cursos, módulos, aulas, provas)
- **Fase 2**: Perfil Aluno (inscrição, consumo de conteúdo)
