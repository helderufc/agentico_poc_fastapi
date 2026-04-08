from celery import Celery
from config import settings

# Registrar todos os models para que o SQLAlchemy resolva os relacionamentos
from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha  # noqa: F401
from br.ufc.llm.curso.domain.curso import Curso  # noqa: F401
from br.ufc.llm.modulo.domain.modulo import Modulo  # noqa: F401
from br.ufc.llm.aula.domain.aula import Aula  # noqa: F401
from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa  # noqa: F401
from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva  # noqa: F401

celery_app = Celery(
    "poc_llm_ufc",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["br.ufc.llm.shared.tasks.ia_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Fortaleza",
    enable_utc=True,
    result_expires=3600,  # resultados expiram em 1 hora
)
