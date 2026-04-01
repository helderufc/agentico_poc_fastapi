from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.modulo.dto.modulo_dto import ModuloEditarRequest, ModuloResponse, ListaModulosResponse
from br.ufc.llm.modulo.service.modulo_service import ModuloService
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException, ModuloAcessoNegadoException
from br.ufc.llm.curso.exception.curso_exception import CursoNaoEncontradoException, CursoAcessoNegadoException

router = APIRouter(prefix="/api/v1", tags=["modulos"])


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


@router.post("/cursos/{curso_id}/modulos", response_model=RespostaPadrao[ModuloResponse], status_code=201)
async def criar_modulo(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        modulo = service.criar_modulo(curso_id, professor_id)
        return RespostaPadrao(data=modulo, message="Módulo criado com sucesso", status=201)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cursos/{curso_id}/modulos", response_model=RespostaPadrao[ListaModulosResponse])
async def listar_modulos(
    curso_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        resultado = service.listar_modulos(curso_id, professor_id)
        return RespostaPadrao(data=resultado, message="Módulos listados com sucesso", status=200)
    except CursoNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cursos/{curso_id}/modulos/{modulo_id}", response_model=RespostaPadrao[ModuloResponse])
async def obter_modulo(
    curso_id: int,
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        modulo = service.obter_modulo(curso_id, modulo_id, professor_id)
        return RespostaPadrao(data=modulo, message="Módulo obtido com sucesso", status=200)
    except (CursoNaoEncontradoException, ModuloNaoEncontradoException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (CursoAcessoNegadoException, ModuloAcessoNegadoException) as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cursos/{curso_id}/modulos/{modulo_id}", response_model=RespostaPadrao[ModuloResponse])
async def editar_modulo(
    curso_id: int,
    modulo_id: int,
    requisicao: ModuloEditarRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        modulo = service.editar_modulo(curso_id, modulo_id, requisicao, professor_id)
        return RespostaPadrao(data=modulo, message="Módulo atualizado com sucesso", status=200)
    except (CursoNaoEncontradoException, ModuloNaoEncontradoException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (CursoAcessoNegadoException, ModuloAcessoNegadoException) as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cursos/{curso_id}/modulos/{modulo_id}", response_model=RespostaPadrao)
async def deletar_modulo(
    curso_id: int,
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        service.deletar_modulo(curso_id, modulo_id, professor_id)
        return RespostaPadrao(data=None, message="Módulo deletado com sucesso", status=200)
    except (CursoNaoEncontradoException, ModuloNaoEncontradoException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (CursoAcessoNegadoException, ModuloAcessoNegadoException) as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cursos/{curso_id}/modulos/{modulo_id}/capa", response_model=RespostaPadrao[ModuloResponse])
async def upload_capa_modulo(
    curso_id: int,
    modulo_id: int,
    arquivo: UploadFile = File(...),
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = ModuloService(session)
        modulo = service.upload_capa(curso_id, modulo_id, professor_id, arquivo)
        return RespostaPadrao(data=modulo, message="Capa enviada com sucesso", status=200)
    except (CursoNaoEncontradoException, ModuloNaoEncontradoException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (CursoAcessoNegadoException, ModuloAcessoNegadoException) as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
