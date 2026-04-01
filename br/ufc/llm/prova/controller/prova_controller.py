from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.prova.dto.prova_dto import (
    ProvaRequest, ProvaResponse, PerguntaRequest, PerguntaResponse,
    EstatisticasProvaResponse, QuizGeradoResponse,
)
from br.ufc.llm.prova.service.prova_service import ProvaService
from br.ufc.llm.prova.exception.prova_exception import (
    ProvaNaoEncontradaException, ProvaJaExisteException,
    PerguntaNaoEncontradaException, PerguntaInvalidaException
)
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException

router = APIRouter(prefix="/api/v1", tags=["provas"])


def _obter_professor_id(authorization: Optional[str] = Header(None), session: Session = Depends(get_db)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = authorization.split(" ")[1]
    try:
        payload = JWTUtil.validar_token(token, tipo_esperado="access")
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return int(usuario_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.post("/modulos/{modulo_id}/prova", response_model=RespostaPadrao[ProvaResponse], status_code=201)
async def criar_prova(
    modulo_id: int,
    requisicao: ProvaRequest = ProvaRequest(),
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        prova = service.criar_prova(modulo_id, requisicao, professor_id)
        return RespostaPadrao(data=prova, message="Prova criada com sucesso", status=201)
    except ModuloNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ProvaJaExisteException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modulos/{modulo_id}/prova", response_model=RespostaPadrao[ProvaResponse])
async def obter_prova(
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        prova = service.obter_prova(modulo_id, professor_id)
        return RespostaPadrao(data=prova, message="Prova obtida com sucesso", status=200)
    except (ModuloNaoEncontradoException, ProvaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modulos/{modulo_id}/prova", response_model=RespostaPadrao[ProvaResponse])
async def editar_prova(
    modulo_id: int,
    requisicao: ProvaRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        prova = service.editar_prova(modulo_id, requisicao, professor_id)
        return RespostaPadrao(data=prova, message="Prova atualizada com sucesso", status=200)
    except (ModuloNaoEncontradoException, ProvaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/modulos/{modulo_id}/prova", response_model=RespostaPadrao)
async def deletar_prova(
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        service.deletar_prova(modulo_id, professor_id)
        return RespostaPadrao(data=None, message="Prova deletada com sucesso", status=200)
    except (ModuloNaoEncontradoException, ProvaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modulos/{modulo_id}/prova/gerar-quiz-ia", response_model=RespostaPadrao[QuizGeradoResponse])
async def gerar_quiz_ia(
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        quiz = service.gerar_quiz_ia(modulo_id, professor_id)
        return RespostaPadrao(data=quiz, message="Quiz gerado com sucesso", status=200)
    except ModuloNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modulos/{modulo_id}/prova/estatisticas", response_model=RespostaPadrao[EstatisticasProvaResponse])
async def obter_estatisticas(
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        estatisticas = service.obter_estatisticas(modulo_id, professor_id)
        return RespostaPadrao(data=estatisticas, message="Estatísticas obtidas com sucesso", status=200)
    except (ModuloNaoEncontradoException, ProvaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/provas/{prova_id}/perguntas", response_model=RespostaPadrao[PerguntaResponse], status_code=201)
async def adicionar_pergunta(
    prova_id: int,
    requisicao: PerguntaRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        pergunta = service.adicionar_pergunta(prova_id, requisicao, professor_id)
        return RespostaPadrao(data=pergunta, message="Pergunta adicionada com sucesso", status=201)
    except ProvaNaoEncontradaException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PerguntaInvalidaException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/provas/{prova_id}/perguntas/{pergunta_id}", response_model=RespostaPadrao[PerguntaResponse])
async def editar_pergunta(
    prova_id: int,
    pergunta_id: int,
    requisicao: PerguntaRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        pergunta = service.editar_pergunta(prova_id, pergunta_id, requisicao, professor_id)
        return RespostaPadrao(data=pergunta, message="Pergunta atualizada com sucesso", status=200)
    except (ProvaNaoEncontradaException, PerguntaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PerguntaInvalidaException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/provas/{prova_id}/perguntas/{pergunta_id}", response_model=RespostaPadrao)
async def deletar_pergunta(
    prova_id: int,
    pergunta_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ProvaService(session)
        service.deletar_pergunta(prova_id, pergunta_id, professor_id)
        return RespostaPadrao(data=None, message="Pergunta deletada com sucesso", status=200)
    except (ProvaNaoEncontradaException, PerguntaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
