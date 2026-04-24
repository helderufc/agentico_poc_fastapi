# Correções de Bloqueio do Event Loop

## Histórico de correções

### Correção 1 — SQLAlchemy síncrono dentro de `async def` (migração anterior)

O código original usava SQLAlchemy síncrono dentro de endpoints `async def`, travando o event loop durante cada query ao banco.

**Solução aplicada:** migração completa para `AsyncSession` + `create_async_engine`, com todos os repositórios e serviços tornando-se `async def` com `await` nas operações de banco.

---

### Correção 2 — I/O de arquivo síncrono dentro de `async def`

#### Problema

Após a migração do banco para async, restavam operações de escrita de arquivo usando `open()` e `f.write()` síncronos dentro de funções `async def`:

```python
# ANTES — bloqueava o event loop durante todo o write
async def atualizar_capa(self, ...):
    conteudo = await arquivo.read()
    with open(caminho, "wb") as f:   # <-- síncrono
        f.write(conteudo)             # <-- síncrono
```

`open()` e `f.write()` são chamadas de sistema bloqueantes. Dentro de uma coroutine, elas travam o event loop inteiro — nenhuma outra requisição é processada até a escrita terminar. Para uploads de PDFs ou imagens (potencialmente MBs), o impacto é proporcional ao tamanho do arquivo.

O mesmo problema ocorria com `Image.open()` em `usuario_service.py`, que além do I/O faz decodificação CPU-bound da imagem.

#### Arquivos afetados

| Arquivo | Linha | Operação bloqueante |
|---|---|---|
| `br/ufc/llm/aula/service/aula_service.py` | 119 | `open/write` — upload de arquivo de aula |
| `br/ufc/llm/curso/service/curso_service.py` | 98 | `open/write` — upload de capa de curso |
| `br/ufc/llm/modulo/service/modulo_service.py` | 104 | `open/write` — upload de capa de módulo |
| `br/ufc/llm/usuario/service/usuario_service.py` | 189 | `Image.open()` — validação de dimensões da foto |
| `br/ufc/llm/usuario/service/usuario_service.py` | 206 | `open/write` — salvar foto de perfil |

#### Solução aplicada

`asyncio.to_thread()` executa a função bloqueante em uma thread do pool de threads do Python, liberando o event loop enquanto o I/O ocorre:

```python
# DEPOIS — event loop livre durante o write
async def atualizar_capa(self, ...):
    conteudo = await arquivo.read()
    await asyncio.to_thread(_salvar_arquivo, caminho, conteudo)
```

A função `_salvar_arquivo` é definida no nível do módulo em cada serviço:

```python
def _salvar_arquivo(caminho: str, conteudo: bytes) -> None:
    with open(caminho, "wb") as f:
        f.write(conteudo)
```

Para `Image.open()`, a função de decodificação captura `conteudo` do escopo externo:

```python
def _obter_dimensoes():
    imagem = Image.open(io.BytesIO(conteudo))
    return imagem.size

width, height = await asyncio.to_thread(_obter_dimensoes)
```

#### Por que não `aiofiles`?

`asyncio.to_thread()` é stdlib (Python 3.9+) e cobre o caso de uso sem adicionar dependência. `aiofiles` seria preferível apenas se houvesse necessidade de streaming incremental de arquivos grandes — aqui os arquivos já estão em memória (`conteudo: bytes`) antes da escrita.

#### Diagrama de concorrência

```
ANTES (open/write síncrono):
Request A ──► await arquivo.read() ──► open()/write() bloqueia ──► Request B aguarda
                                              (event loop travado)

DEPOIS (asyncio.to_thread):
Request A ──► await arquivo.read() ──► to_thread(write) ──► event loop livre
                                              └──────────────────► Request B processada
```
