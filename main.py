from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import Base, engine

# Importar models para garantir que sejam registrados no metadata
from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha
from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.modulo.domain.modulo import Modulo
from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa

from br.ufc.llm.usuario.controller.usuario_controller import router as usuario_router
from br.ufc.llm.curso.controller.curso_controller import router as curso_router
from br.ufc.llm.modulo.controller.modulo_controller import router as modulo_router
from br.ufc.llm.aula.controller.aula_controller import router as aula_router
from br.ufc.llm.prova.controller.prova_controller import router as prova_router
from br.ufc.llm.matricula.controller.matricula_controller import router as matricula_router
from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva
from br.ufc.llm.shared.controller.task_controller import router as task_router

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Inicializar aplicação
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
    description="API REST para PoC LLM UFC",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(usuario_router)
app.include_router(curso_router)
app.include_router(modulo_router)
app.include_router(aula_router)
app.include_router(prova_router)
app.include_router(matricula_router)
app.include_router(task_router)


@app.get("/")
async def root():
    return {"message": "PoC LLM UFC - API rodando"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
