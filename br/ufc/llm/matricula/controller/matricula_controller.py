from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.matricula.dto.matricula_dto import (
    MatriculaRequest,
    MatriculaResponse,
    ListaMatriculasResponse,
    ListaCatalogoCursosResponse,
    CursoResumidoResponse,
    ListaModulosResponse,
    ListaAulasResponse,
    AulaCompletaResponse,
    ProvaSemGabaritoResponse,
    ResultadoProvaResponse,
    RespostaItemRequest,
)
from br.ufc.llm.matricula.service.matricula_service import MatriculaService
from br.ufc.llm.matricula.exception.matricula_exception import (
    MatriculaException,
    MatriculaJaExisteException,
    MatriculaNaoEncontradaException,
    CursoNaoPublicadoException,
    AcessoNegadoMatriculaException,
    PerfilInvalidoException,
    DadosMatriculaObrigatoriosException,
    RespostaJaExisteException,
    RespostasIncompletasException,
    ResultadoNaoEncontradoException,
)

router = APIRouter(prefix="/api/v1", tags=["matriculas"])


def _obter_payload(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = authorization.split(" ")[1]
    try:
        return JWTUtil.validar_token(token, tipo_esperado="access")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


# ==================== CATÁLOGO ====================

@router.get("/catalogo/cursos", response_model=RespostaPadrao[ListaCatalogoCursosResponse])
async def listar_catalogo(
    q: Optional[str] = Query(None),
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    service = MatriculaService(session)
    resultado = service.listar_catalogo(q)
    return RespostaPadrao(data=resultado, message="Catálogo listado com sucesso", status=200)


@router.get("/catalogo/cursos/{curso_id}", response_model=RespostaPadrao[CursoResumidoResponse])
async def obter_curso_catalogo(
    curso_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        service = MatriculaService(session)
        curso = service.obter_curso_publicado(curso_id)
        return RespostaPadrao(data=curso, message="Curso obtido com sucesso", status=200)
    except CursoNaoPublicadoException as e:
        raise HTTPException(status_code=404, detail=e.message)


# ==================== MATRÍCULA ====================

@router.post("/matriculas", response_model=RespostaPadrao[MatriculaResponse], status_code=201)
async def matricular(
    requisicao: MatriculaRequest,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        perfil = payload.get("perfil")
        service = MatriculaService(session)
        matricula = service.matricular(aluno_id, perfil, requisicao)
        return RespostaPadrao(data=matricula, message="Matrícula realizada com sucesso", status=201)
    except PerfilInvalidoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except CursoNaoPublicadoException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except MatriculaJaExisteException as e:
        raise HTTPException(status_code=409, detail=e.message)
    except DadosMatriculaObrigatoriosException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/matriculas", response_model=RespostaPadrao[ListaMatriculasResponse])
async def listar_minhas_matriculas(
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    aluno_id = int(payload.get("sub"))
    service = MatriculaService(session)
    resultado = service.listar_minhas_matriculas(aluno_id)
    return RespostaPadrao(data=resultado, message="Matrículas listadas com sucesso", status=200)


# ==================== CONTEÚDO ====================

@router.get("/matriculas/{curso_id}/modulos", response_model=RespostaPadrao[ListaModulosResponse])
async def listar_modulos(
    curso_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        resultado = service.listar_modulos(aluno_id, curso_id)
        return RespostaPadrao(data=resultado, message="Módulos listados com sucesso", status=200)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get(
    "/matriculas/{curso_id}/modulos/{modulo_id}/aulas",
    response_model=RespostaPadrao[ListaAulasResponse]
)
async def listar_aulas(
    curso_id: int,
    modulo_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        resultado = service.listar_aulas(aluno_id, curso_id, modulo_id)
        return RespostaPadrao(data=resultado, message="Aulas listadas com sucesso", status=200)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get(
    "/matriculas/{curso_id}/modulos/{modulo_id}/aulas/{aula_id}",
    response_model=RespostaPadrao[AulaCompletaResponse]
)
async def obter_aula(
    curso_id: int,
    modulo_id: int,
    aula_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        aula = service.obter_aula(aluno_id, curso_id, modulo_id, aula_id)
        return RespostaPadrao(data=aula, message="Aula obtida com sucesso", status=200)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except MatriculaNaoEncontradaException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get(
    "/matriculas/{curso_id}/modulos/{modulo_id}/prova",
    response_model=RespostaPadrao[ProvaSemGabaritoResponse]
)
async def obter_prova(
    curso_id: int,
    modulo_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        prova = service.obter_prova(aluno_id, curso_id, modulo_id)
        return RespostaPadrao(data=prova, message="Prova obtida com sucesso", status=200)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except MatriculaNaoEncontradaException as e:
        raise HTTPException(status_code=404, detail=e.message)


# ==================== PROVA ====================

@router.post("/provas/{prova_id}/responder", status_code=201, response_model=RespostaPadrao)
async def responder_prova(
    prova_id: int,
    respostas: List[RespostaItemRequest],
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        service.responder_prova(aluno_id, prova_id, respostas)
        return RespostaPadrao(data=None, message="Respostas registradas com sucesso", status=201)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except RespostaJaExisteException as e:
        raise HTTPException(status_code=409, detail=e.message)
    except RespostasIncompletasException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except MatriculaNaoEncontradaException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/provas/{prova_id}/resultado", response_model=RespostaPadrao[ResultadoProvaResponse])
async def obter_resultado(
    prova_id: int,
    payload: dict = Depends(_obter_payload),
    session: Session = Depends(get_db)
):
    try:
        aluno_id = int(payload.get("sub"))
        service = MatriculaService(session)
        resultado = service.obter_resultado(aluno_id, prova_id)
        return RespostaPadrao(data=resultado, message="Resultado obtido com sucesso", status=200)
    except AcessoNegadoMatriculaException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ResultadoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except MatriculaNaoEncontradaException as e:
        raise HTTPException(status_code=404, detail=e.message)
