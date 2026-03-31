# Requisitos Não Funcionais — PoC LLM UFC

- **RNF01** – FastAPI com Python 3.12.3
- **RNF02** – Autenticação stateless com JWT: access token (curta duração) + refresh token (longa duração)
- **RNF03** – Documentação automática
- **RNF04** – Banco PostgreSQL 16+ com Alembic
- **RNF05** – Upload de arquivos local com validação
- **RNF06** – Senhas armazenadas com BCrypt
- **RNF07** – HTML do CKEditor sanitizado via Bleach
- **RNF08** – Listagens de cursos paginadas
- **RNF09** – Respostas da API padronizadas: `{ data, message, status }` com códigos HTTP corretos
- **RNF10** – Integração com OpenAI GPT-4o
- **RNF11** – Extração de texto de PDFs via pypdf
- **RNF12** – Mapeamento Entidade
- **RNF13** – Envio de e-mails transacionais
