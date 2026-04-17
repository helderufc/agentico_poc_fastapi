from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao
from br.ufc.llm.shared.domain.seguranca import JWTUtil
from br.ufc.llm.usuario.dto.usuario_dto import (
    UsuarioCadastroRequest,
    UsuarioLoginRequest,
    UsuarioResponse,
    TokenResponse,
    AlterarSenhaRequest,
    RefreshTokenRequest,
    ListaUsuariosResponse
)
from br.ufc.llm.usuario.service.usuario_service import UsuarioService
from br.ufc.llm.usuario.exception.usuario_exception import UsuarioException
from config import settings

router = APIRouter(prefix="/api/v1", tags=["autenticacao"])


async def obter_usuario_atual(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db)
) -> UsuarioResponse:
    if settings.LOAD_TEST_MODE:
        service = UsuarioService(session)
        return await service.obter_perfil(settings.LOAD_TEST_PROFESSOR_ID)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1]

    try:
        payload = JWTUtil.validar_token(token, tipo_esperado="access")
        usuario_id = payload.get("sub")

        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        service = UsuarioService(session)
        usuario = await service.obter_perfil(usuario_id)
        return usuario
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def require_admin(usuario: UsuarioResponse = Depends(obter_usuario_atual)) -> UsuarioResponse:
    if settings.LOAD_TEST_MODE:
        return usuario
    if usuario.perfil != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return usuario


@router.post("/auth/cadastro", response_model=RespostaPadrao[UsuarioResponse], status_code=201)
async def cadastro(
    requisicao: UsuarioCadastroRequest,
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        service = UsuarioService(session)
        usuario = await service.cadastrar_usuario(requisicao)
        return RespostaPadrao(
            data=usuario,
            message="Usuário cadastrado com sucesso. Aguarde ativação de um administrador.",
            status=201
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar usuário: {str(e)}")


@router.post("/auth/login", response_model=RespostaPadrao[TokenResponse])
async def login(
    requisicao: UsuarioLoginRequest,
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[TokenResponse]:
    try:
        service = UsuarioService(session)
        tokens = await service.login(requisicao)
        return RespostaPadrao(data=tokens, message="Login realizado com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer login: {str(e)}")


@router.post("/auth/refresh", response_model=RespostaPadrao[TokenResponse])
async def refresh_token(
    requisicao: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[TokenResponse]:
    try:
        service = UsuarioService(session)
        tokens = await service.refresh_token(requisicao.refresh_token)
        return RespostaPadrao(data=tokens, message="Token renovado com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao renovar token: {str(e)}")


@router.post("/auth/recuperar-senha", response_model=RespostaPadrao)
async def recuperar_senha(
    email: str = Query(..., description="E-mail do usuário"),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao:
    try:
        service = UsuarioService(session)
        await service.solicitar_recuperacao_senha(email)
        return RespostaPadrao(
            data=None,
            message="Se o e-mail existe na base, um link de recuperação será enviado",
            status=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao solicitar recuperação: {str(e)}")


@router.post("/auth/redefinir-senha", response_model=RespostaPadrao[UsuarioResponse])
async def redefinir_senha(
    token: str = Query(..., description="Token de recuperação"),
    nova_senha: str = Query(..., description="Nova senha"),
    confirmacao_senha: str = Query(..., description="Confirmação da nova senha"),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        if nova_senha != confirmacao_senha:
            raise HTTPException(status_code=400, detail="Senhas não conferem")

        service = UsuarioService(session)
        usuario = await service.redefinir_senha(token, nova_senha)
        return RespostaPadrao(data=usuario, message="Senha redefinida com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao redefinir senha: {str(e)}")


@router.get("/perfil", response_model=RespostaPadrao[UsuarioResponse])
async def obter_perfil_endpoint(
    usuario: UsuarioResponse = Depends(obter_usuario_atual)
) -> RespostaPadrao[UsuarioResponse]:
    return RespostaPadrao(data=usuario, message="Perfil obtido com sucesso", status=200)


@router.put("/perfil/foto", response_model=RespostaPadrao[UsuarioResponse])
async def upload_foto_perfil(
    arquivo: UploadFile = File(...),
    usuario: UsuarioResponse = Depends(obter_usuario_atual),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        service = UsuarioService(session)
        caminho = await service.upload_foto_perfil(usuario.id, arquivo)
        usuario_atualizado = await service.obter_perfil(usuario.id)
        return RespostaPadrao(
            data=usuario_atualizado,
            message=f"Foto enviada com sucesso: {caminho}",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@router.put("/perfil/senha", response_model=RespostaPadrao[UsuarioResponse])
async def alterar_senha(
    requisicao: AlterarSenhaRequest,
    usuario: UsuarioResponse = Depends(obter_usuario_atual),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        service = UsuarioService(session)
        usuario_atualizado = await service.alterar_senha(usuario.id, requisicao)
        return RespostaPadrao(data=usuario_atualizado, message="Senha alterada com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao alterar senha: {str(e)}")


@router.get("/admin/usuarios", response_model=RespostaPadrao[ListaUsuariosResponse])
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    usuario_admin: UsuarioResponse = Depends(require_admin),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[ListaUsuariosResponse]:
    try:
        service = UsuarioService(session)
        resultado = await service.listar_usuarios_paginated(skip, limit)
        return RespostaPadrao(
            data=resultado,
            message=f"Listando usuários ({resultado.total} no total)",
            status=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar usuários: {str(e)}")


@router.patch("/admin/usuarios/{usuario_id}/ativar", response_model=RespostaPadrao[UsuarioResponse])
async def ativar_usuario(
    usuario_id: int,
    usuario_admin: UsuarioResponse = Depends(require_admin),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        service = UsuarioService(session)
        usuario = await service.ativar_usuario(usuario_id)
        return RespostaPadrao(data=usuario, message=f"Usuário {usuario.nome} ativado com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ativar usuário: {str(e)}")


@router.patch("/admin/usuarios/{usuario_id}/desativar", response_model=RespostaPadrao[UsuarioResponse])
async def desativar_usuario(
    usuario_id: int,
    usuario_admin: UsuarioResponse = Depends(require_admin),
    session: AsyncSession = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    try:
        service = UsuarioService(session)
        usuario = await service.desativar_usuario(usuario_id)
        return RespostaPadrao(data=usuario, message=f"Usuário {usuario.nome} desativado com sucesso", status=200)
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desativar usuário: {str(e)}")
