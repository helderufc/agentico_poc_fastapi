import os
import re

from br.ufc.llm.shared.service.celery_app import celery_app
from database import SessionLocal


@celery_app.task(bind=True, name="ia_tasks.gerar_conteudo_aula")
def gerar_conteudo_aula_task(self, modulo_id: int, aula_id: int, professor_id: int) -> dict:
    """Gera conteúdo HTML via IA para uma aula (executado em background)."""
    from br.ufc.llm.shared.service.openai_service import gerar_conteudo_aula, extrair_texto_pdf
    from br.ufc.llm.aula.service.aula_service import AulaService
    from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
    from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException
    from br.ufc.llm.aula.exception.aula_exception import AulaNaoEncontradaException

    session = SessionLocal()
    try:
        service = AulaService(session)
        resultado = service.gerar_conteudo(modulo_id, aula_id, professor_id)
        return {"conteudo_gerado": resultado.conteudo_gerado}
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise ValueError(e.message)
    except (CursoAcessoNegadoException,) as e:
        raise PermissionError(e.message)
    finally:
        session.close()


@celery_app.task(bind=True, name="ia_tasks.gerar_quiz_ia", autoretry_for=(ValueError,), retry_kwargs={"max_retries": 2}, retry_backoff=2)
def gerar_quiz_ia_task(self, modulo_id: int, professor_id: int, num_perguntas: int = 5) -> dict:
    """Gera quiz via IA a partir do conteúdo do módulo (executado em background)."""
    from br.ufc.llm.prova.service.prova_service import ProvaService
    from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
    from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException

    session = SessionLocal()
    try:
        service = ProvaService(session)
        resultado = service.gerar_quiz_ia(modulo_id, professor_id, num_perguntas)
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
    except (ModuloNaoEncontradoException,) as e:
        raise ValueError(e.message)
    except (CursoAcessoNegadoException,) as e:
        raise PermissionError(e.message)
    finally:
        session.close()
