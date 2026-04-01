from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.aula.dto.aula_dto import (
    AulaRequest, AulaEditarRequest, AulaResponse, ListaAulasResponse,
    ConteudoGeradoResponse, ConfirmarConteudoRequest,
)
from br.ufc.llm.aula.service.aula_service import AulaService
from br.ufc.llm.aula.exception.aula_exception import AulaNaoEncontradaException
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException

router = APIRouter(prefix="/api/v1", tags=["aulas"])


def _obter_professor_id(authorization: Optional[str] = Header(None)) -> int:
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


@router.post("/modulos/{modulo_id}/aulas", response_model=RespostaPadrao[AulaResponse], status_code=201)
async def criar_aula(
    modulo_id: int,
    requisicao: AulaRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        aula = service.criar_aula(modulo_id, requisicao, professor_id)
        return RespostaPadrao(data=aula, message="Aula criada com sucesso", status=201)
    except ModuloNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modulos/{modulo_id}/aulas", response_model=RespostaPadrao[ListaAulasResponse])
async def listar_aulas(
    modulo_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        resultado = service.listar_aulas(modulo_id, professor_id)
        return RespostaPadrao(data=resultado, message="Aulas listadas com sucesso", status=200)
    except ModuloNaoEncontradoException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modulos/{modulo_id}/aulas/{aula_id}", response_model=RespostaPadrao[AulaResponse])
async def obter_aula(
    modulo_id: int,
    aula_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        aula = service.obter_aula(modulo_id, aula_id, professor_id)
        return RespostaPadrao(data=aula, message="Aula obtida com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modulos/{modulo_id}/aulas/{aula_id}", response_model=RespostaPadrao[AulaResponse])
async def editar_aula(
    modulo_id: int,
    aula_id: int,
    requisicao: AulaEditarRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        aula = service.editar_aula(modulo_id, aula_id, requisicao, professor_id)
        return RespostaPadrao(data=aula, message="Aula atualizada com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/modulos/{modulo_id}/aulas/{aula_id}", response_model=RespostaPadrao)
async def deletar_aula(
    modulo_id: int,
    aula_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        service.deletar_aula(modulo_id, aula_id, professor_id)
        return RespostaPadrao(data=None, message="Aula deletada com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/modulos/{modulo_id}/aulas/{aula_id}/gerar-conteudo",
    response_model=RespostaPadrao[ConteudoGeradoResponse]
)
async def gerar_conteudo(
    modulo_id: int,
    aula_id: int,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        resultado = service.gerar_conteudo(modulo_id, aula_id, professor_id)
        return RespostaPadrao(data=resultado, message="Conteúdo gerado com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/modulos/{modulo_id}/aulas/{aula_id}/confirmar-conteudo",
    response_model=RespostaPadrao[AulaResponse]
)
async def confirmar_conteudo(
    modulo_id: int,
    aula_id: int,
    requisicao: ConfirmarConteudoRequest,
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        aula = service.confirmar_conteudo(modulo_id, aula_id, professor_id, requisicao)
        return RespostaPadrao(data=aula, message="Conteúdo confirmado e salvo com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modulos/{modulo_id}/aulas/{aula_id}/arquivo", response_model=RespostaPadrao[AulaResponse])
async def upload_arquivo(
    modulo_id: int,
    aula_id: int,
    arquivo: UploadFile = File(...),
    professor_id: int = Depends(_obter_professor_id),
    session: Session = Depends(get_db)
):
    try:
        service = AulaService(session)
        aula = service.upload_arquivo(modulo_id, aula_id, professor_id, arquivo)
        return RespostaPadrao(data=aula, message="Arquivo enviado com sucesso", status=200)
    except (ModuloNaoEncontradoException, AulaNaoEncontradaException) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CursoAcessoNegadoException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
