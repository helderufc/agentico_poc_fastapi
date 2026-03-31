# Arquitetura — PoC LLM UFC

## Decisões de Arquitetura

| Decisão | Escolha |
|---|---|
| Upload de arquivos | Local no servidor (disco) |
| Categorias de curso | Dinâmicas com deduplicação case-insensitive |
| Prova | Vinculada ao módulo (1:1) |
| Conteúdo da aula | Arquivo + CKEditor coexistem |
| Pacote raiz | `br.ufc.llm` |

## Entidades e Relacionamentos

```
Usuario (1) ──> (N) Curso            [professor_id FK]
Curso   (1) ──> (N) Modulo           [curso_id FK, ON DELETE CASCADE]
Modulo  (1) ──> (N) Aula             [modulo_id FK, ON DELETE CASCADE]
Modulo  (1) ──> (0..1) Prova         [modulo_id FK UNIQUE, ON DELETE CASCADE]
Prova   (1) ──> (N) Pergunta         [prova_id FK, ON DELETE CASCADE]
Pergunta(1) ──> (N) Alternativa      [pergunta_id FK, ON DELETE CASCADE]
Usuario (1) ──> (N) TokenRecuperacao [usuario_id FK]
```

## Tabelas do Banco (PostgreSQL)

```sql
CREATE TABLE usuarios (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(255) NOT NULL,
    cpf         VARCHAR(14)  NOT NULL UNIQUE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    senha       VARCHAR(255) NOT NULL,             -- BCrypt
    perfil      VARCHAR(20)  NOT NULL,             -- PROFESSOR | ALUNO | ADMIN
    status      VARCHAR(10)  NOT NULL DEFAULT 'INATIVO',
    foto_perfil VARCHAR(500),                      -- path local
    criado_em   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE tokens_recuperacao_senha (
    id         BIGSERIAL    PRIMARY KEY,
    token      VARCHAR(255) NOT NULL UNIQUE,
    expiracao  TIMESTAMP    NOT NULL,
    usado      BOOLEAN      NOT NULL DEFAULT FALSE,
    usuario_id BIGINT       NOT NULL REFERENCES usuarios(id)
);

CREATE TABLE cursos (
    id              BIGSERIAL    PRIMARY KEY,
    titulo          VARCHAR(255) NOT NULL,
    categoria       VARCHAR(100) NOT NULL,
    descricao       TEXT         NOT NULL,
    carga_horaria   VARCHAR(20)  NOT NULL,         -- ex: "30h"
    capa            VARCHAR(500),                  -- path local
    status          VARCHAR(20)  NOT NULL DEFAULT 'RASCUNHO',
    requer_endereco BOOLEAN      NOT NULL DEFAULT FALSE,
    requer_genero   BOOLEAN      NOT NULL DEFAULT FALSE,
    requer_idade    BOOLEAN      NOT NULL DEFAULT FALSE,
    professor_id    BIGINT       NOT NULL REFERENCES usuarios(id),
    criado_em       TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE modulos (
    id       BIGSERIAL   PRIMARY KEY,
    nome     VARCHAR(50) NOT NULL,                 -- "Módulo 01", "Módulo 02"...
    ordem    INT         NOT NULL,
    capa     VARCHAR(500),
    curso_id BIGINT      NOT NULL REFERENCES cursos(id) ON DELETE CASCADE
);

CREATE TABLE aulas (
    id                 BIGSERIAL    PRIMARY KEY,
    nome               VARCHAR(255) NOT NULL,
    ordem              INT          NOT NULL,
    arquivo            VARCHAR(500),               -- path local
    tipo_arquivo       VARCHAR(10),                -- PDF | VIDEO
    conteudo_ck_editor TEXT,                       -- HTML digitado pelo professor
    conteudo_gerado    TEXT,                       -- HTML gerado e confirmado pela IA
    modulo_id          BIGINT       NOT NULL REFERENCES modulos(id) ON DELETE CASCADE
);

CREATE TABLE provas (
    id                         BIGSERIAL PRIMARY KEY,
    modulo_id                  BIGINT    NOT NULL UNIQUE REFERENCES modulos(id) ON DELETE CASCADE,
    mostrar_respostas_erradas  BOOLEAN   NOT NULL DEFAULT FALSE,
    mostrar_respostas_corretas BOOLEAN   NOT NULL DEFAULT FALSE,
    mostrar_valores            BOOLEAN   NOT NULL DEFAULT FALSE
);

CREATE TABLE perguntas (
    id        BIGSERIAL PRIMARY KEY,
    enunciado TEXT      NOT NULL,
    pontos    INT       NOT NULL DEFAULT 1,
    ordem     INT       NOT NULL,
    prova_id  BIGINT    NOT NULL REFERENCES provas(id) ON DELETE CASCADE
);

CREATE TABLE alternativas (
    id          BIGSERIAL PRIMARY KEY,
    texto       TEXT      NOT NULL,
    correta     BOOLEAN   NOT NULL DEFAULT FALSE,
    pergunta_id BIGINT    NOT NULL REFERENCES perguntas(id) ON DELETE CASCADE
);
```

## Endpoints REST

### Auth
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/auth/cadastro` | Cadastrar professor ou aluno |
| POST | `/auth/login` | Login → access + refresh token |
| POST | `/auth/refresh` | Renovar access token |
| POST | `/auth/recuperar-senha` | Solicitar token por e-mail |
| POST | `/auth/redefinir-senha` | Redefinir senha com token |

### Perfil
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/perfil` | Dados do usuário logado |
| PUT | `/perfil/foto` | Upload de foto de perfil |
| PUT | `/perfil/senha` | Alterar senha (requer senha atual) |

### Admin
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/admin/usuarios` | Listar todos os usuários |
| PATCH | `/admin/usuarios/{id}/ativar` | Ativar conta |
| PATCH | `/admin/usuarios/{id}/desativar` | Desativar conta |

### Cursos
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/cursos` | Listar cursos do professor (paginado) |
| POST | `/cursos` | Criar curso |
| GET | `/cursos/{id}` | Buscar por ID |
| PUT | `/cursos/{id}` | Editar curso |
| DELETE | `/cursos/{id}` | Excluir curso |
| PATCH | `/cursos/{id}/status` | Alterar status |
| GET | `/cursos/buscar?q=termo` | Buscar por texto |

### Módulos
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/cursos/{cursoId}/modulos` | Adicionar módulo |
| PUT | `/modulos/{id}` | Editar módulo |
| DELETE | `/modulos/{id}` | Excluir (renumera os demais) |
| PATCH | `/modulos/{id}/ordem` | Reordenar |

### Aulas
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/modulos/{moduloId}/aulas` | Adicionar aula |
| PUT | `/aulas/{id}` | Editar aula |
| DELETE | `/aulas/{id}` | Excluir aula |
| PATCH | `/aulas/{id}/ordem` | Reordenar |
| POST | `/aulas/{id}/gerar-conteudo` | Spring AI: gera conteúdo (preview) |
| POST | `/aulas/{id}/confirmar-conteudo` | Salvar conteúdo gerado pela IA |

### Provas
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/modulos/{moduloId}/prova` | Criar prova |
| GET | `/modulos/{moduloId}/prova` | Buscar prova |
| PUT | `/provas/{id}` | Editar configurações |
| DELETE | `/provas/{id}` | Excluir prova |
| POST | `/modulos/{moduloId}/prova/gerar-quiz-ia` | Spring AI: gera quiz (não salva) |

### Perguntas
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/provas/{provaId}/perguntas` | Adicionar pergunta |
| PUT | `/perguntas/{id}` | Editar |
| DELETE | `/perguntas/{id}` | Excluir |

### Alternativas
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/perguntas/{perguntaId}/alternativas` | Adicionar alternativa |
| PUT | `/alternativas/{id}` | Editar |
| DELETE | `/alternativas/{id}` | Excluir |
