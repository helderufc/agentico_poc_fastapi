import asyncio

from br.ufc.llm.shared.service.celery_app import celery_app
from database import AsyncSessionLocal


@celery_app.task(bind=True, name="ia_tasks.gerar_conteudo_aula")
def gerar_conteudo_aula_task(self, modulo_id: int, aula_id: int, professor_id: int) -> dict:
    async def _run():
        from br.ufc.llm.aula.service.aula_service import AulaService
        from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
        from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException
        from br.ufc.llm.aula.exception.aula_exception import AulaNaoEncontradaException

        async with AsyncSessionLocal() as session:
            service = AulaService(session)
            resultado = await service.gerar_conteudo(modulo_id, aula_id, professor_id)
            return {"conteudo_gerado": resultado.conteudo_gerado}

    try:
        return asyncio.run(_run())
    except (ModuloNaoEncontradoException if False else Exception) as e:
        # Re-raise domain exceptions as ValueError/PermissionError for Celery
        name = type(e).__name__
        if "NaoEncontrado" in name or "NaoEncontrada" in name:
            raise ValueError(str(e))
        if "AcessoNegado" in name:
            raise PermissionError(str(e))
        raise


@celery_app.task(bind=True, name="ia_tasks.gerar_quiz_ia", autoretry_for=(ValueError,), retry_kwargs={"max_retries": 2}, retry_backoff=2)
def gerar_quiz_ia_task(self, modulo_id: int, professor_id: int, num_perguntas: int = 5) -> dict:
    async def _run():
        from br.ufc.llm.prova.service.prova_service import ProvaService

        async with AsyncSessionLocal() as session:
            service = ProvaService(session)
            resultado = await service.gerar_quiz_ia(modulo_id, professor_id, num_perguntas)
            return {
                "perguntas": [
                    {
                        "enunciado": p.enunciado,
                        "pontos": p.pontos,
                        "alternativas": [
                            {"texto": a.texto, "correta": a.correta}
                            for a in p.alternativas
                        ],
                    }
                    for p in resultado.perguntas
                ]
            }

    try:
        return asyncio.run(_run())
    except Exception as e:
        name = type(e).__name__
        if "NaoEncontrado" in name or "NaoEncontrada" in name:
            raise ValueError(str(e))
        if "AcessoNegado" in name:
            raise PermissionError(str(e))
        raise
