# Setup do Projeto - Próximos Passos

## ✅ Etapas Concluídas

1. ✓ Criada estrutura de pacotes (br.ufc.llm.*)
2. ✓ Configurado FastAPI com CORS
3. ✓ Estruturado banco de dados (SQLAlchemy + Alembic)
4. ✓ Criados arquivos de configuração (.env.example)
5. ✓ Estrutura de testes com pytest

## 📋 Próximas Etapas

### 1. Instalar Dependências
```bash
./venv/bin/pip install -r requirements.txt
```

### 2. Configurar Banco de Dados
```bash
# Criar banco PostgreSQL
createdb llm_ufc

# Configurar .env com credenciais
cp .env.example .env
# Editar .env com DATABASE_URL correto
```

### 3. Implementar Modelo de Usuário (Fase 1)
- [ ] Criar models.py com entidade Usuario
- [ ] Criar DTO UsuarioRequest/UsuarioResponse
- [ ] Implementar autenticação (JWT + bcrypt)
- [ ] Criar endpoints de login/register
- [ ] Criar testes para autenticação

### 4. Implementar Perfil Professor
- [ ] Criar models para Curso, Modulo, Aula, Prova
- [ ] Implementar endpoints CRUD para cada entidade
- [ ] Integração com OpenAI para geração de conteúdo
- [ ] Testes de negócio

## 🚀 Rodar Aplicação

```bash
python main.py
# ou
./venv/bin/python main.py
```

API disponível em: http://localhost:8000
Docs: http://localhost:8000/docs

## 📁 Estrutura Atual

```
.
├── br/ufc/llm/          # Pacotes principais
│   ├── usuario/
│   ├── curso/
│   ├── modulo/
│   ├── aula/
│   ├── prova/
│   └── shared/          # Código compartilhado
├── migrations/          # Migrações Alembic
├── tests/               # Testes automatizados
├── main.py              # Aplicação FastAPI
├── config.py            # Configurações
├── database.py          # Conexão com DB
├── requirements.txt     # Dependências Python
├── README.md            # Documentação
└── .env.example         # Template de variáveis ambiente
```

## 💡 Comandos Úteis

```bash
# Criar migração
./venv/bin/alembic revision --autogenerate -m "Descição da mudança"

# Aplicar migrações
./venv/bin/alembic upgrade head

# Reverter última migração
./venv/bin/alembic downgrade -1

# Rodar testes
./venv/bin/pytest

# Rodar testes com cobertura
./venv/bin/pytest --cov=br/ufc/llm
```

## ⚠️ Avisos Importantes

- **Segurança**: Alterar SECRET_KEY antes de ir para produção
- **Banco de Dados**: PostgreSQL 16 deve estar rodando
- **OpenAI**: Configurar OPENAI_API_KEY antes de usar IA
- **Redis**: Necessário para fila de jobs (RQ)

---

Próximo passo: Instalar dependências e começar com modelos de usuário!
