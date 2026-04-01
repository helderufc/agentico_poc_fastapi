from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Header
from sqlalchemy.orm import Session

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.curso.dto.curso_dto import CursoRequest, CursoResponse, ListaCursosResponse
from br.ufc.llm.curso.service.curso_service import CursoService
from br.ufc.llm.curso.exception.curso_exception import CursoNaoEncontradoException, CursoAcessoNegadoException

router = APIRouter(prefix="/api/v1", tags=["cursos"])


def _obter_professor_id(authorization: Optional[str] = Header(None), session: Session = Depends(get_db)) -> int:
    """Extrai o professor_id do JWT"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = authorization.split(" ")[1]
    try:
        payload = JWTUtil.validar_token(token, tipo_esperado="access")
        usuario_id = payload.get("sub")
        perfil = payload.get("perfil")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        if perfil not in ("PROFESSOR", "ADMIN"):
            raise HTTPException(status_code=403, detail="Apenas professores podem gerenciar cursos")
        return int(usuario_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.post("/cursos", response_model=RespostaPadrao[CursoResponse], status_code=201)
async def criar_curso(
    requisicao: CursoRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.criar_curso(requisicao, professor_id)
        return RespostaPadrao(data=curso, message="Curso criado com sucesso", status=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cursos", response_model=RespostaPadrao[ListaCursosResponse])
async def listar_cursos(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        resultado = service.listar_cursos(professor_id, status, q)
        return RespostaPadrao(data=resultado, message="Cursos listados com sucesso", status=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cursos/{curso_id}", response_model=RespostaPadrao[CursoResponse])
async def obter_curso(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.obter_curso(curso_id, professor_id)
        return RespostaPadrao(data=curso, message="Curso obtido com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cursos/{curso_id}", response_model=RespostaPadrao[CursoResponse])
async def editar_curso(
    curso_id: int,
    requisicao: CursoRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.editar_curso(curso_id, requisicao, professor_id)
        return RespostaPadrao(data=curso, message="Curso atualizado com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cursos/{curso_id}", response_model=RespostaPadrao)
async def deletar_curso(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        service.deletar_curso(curso_id, professor_id)
        return RespostaPadrao(data=None, message="Curso deletado com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cursos/{curso_id}/capa", response_model=RespostaPadrao[CursoResponse])
async def upload_capa(
    curso_id: int,
    arquivo: UploadFile = File(...),
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.upload_capa(curso_id, professor_id, arquivo)
        return RespostaPadrao(data=curso, message="Capa enviada com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/cursos/{curso_id}/publicar", response_model=RespostaPadrao[CursoResponse])
async def publicar_curso(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.publicar_curso(curso_id, professor_id)
        return RespostaPadrao(data=curso, message="Curso publicado com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/cursos/{curso_id}/arquivar", response_model=RespostaPadrao[CursoResponse])
async def arquivar_curso(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = CursoService(session)
        curso = service.arquivar_curso(curso_id, professor_id)
        return RespostaPadrao(data=curso, message="Curso arquivado com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
