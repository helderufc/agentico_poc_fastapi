from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Header
from typing import Optional
from sqlalchemy.orm import Session

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


# ==================== DEPENDÊNCIAS ====================

async def obter_usuario_atual(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_db)
) -> UsuarioResponse:
    """
    Dependency para extrair usuário atual do JWT
    Uso: get_current_user = Depends(obter_usuario_atual)
    """
    if settings.LOAD_TEST_MODE:
        service = UsuarioService(session)
        return service.obter_perfil(settings.LOAD_TEST_PROFESSOR_ID)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1]

    try:
        payload = JWTUtil.validar_token(token, tipo_esperado="access")
        usuario_id = payload.get("sub")

        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Buscar usuário no BD
        service = UsuarioService(session)
        usuario = service.obter_perfil(usuario_id)
        return usuario
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def require_admin(usuario: UsuarioResponse = Depends(obter_usuario_atual)) -> UsuarioResponse:
    """Dependency para validar se usuário é ADMIN"""
    if settings.LOAD_TEST_MODE:
        return usuario
    if usuario.perfil != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return usuario


# ==================== ENDPOINTS DE AUTENTICAÇÃO ====================

@router.post("/auth/cadastro", response_model=RespostaPadrao[UsuarioResponse], status_code=201)
async def cadastro(
    requisicao: UsuarioCadastroRequest,
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Cadastrar novo usuário (RF01)
    - Nome, CPF, email, senha, perfil
    - Status inicia como INATIVO (RN01)
    """
    try:
        service = UsuarioService(session)
        usuario = service.cadastrar_usuario(requisicao)

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
    session: Session = Depends(get_db)
) -> RespostaPadrao[TokenResponse]:
    """
    Autenticar usuário e gerar tokens JWT (RF02)
    - Requer email/nome + senha
    - Usuário deve estar ATIVO (RN01)
    - Retorna access_token + refresh_token
    """
    try:
        service = UsuarioService(session)
        tokens = service.login(requisicao)

        return RespostaPadrao(
            data=tokens,
            message="Login realizado com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer login: {str(e)}")


@router.post("/auth/refresh", response_model=RespostaPadrao[TokenResponse])
async def refresh_token(
    requisicao: RefreshTokenRequest,
    session: Session = Depends(get_db)
) -> RespostaPadrao[TokenResponse]:
    """
    Renovar access token usando refresh token
    """
    try:
        service = UsuarioService(session)
        tokens = service.refresh_token(requisicao.refresh_token)

        return RespostaPadrao(
            data=tokens,
            message="Token renovado com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao renovar token: {str(e)}")


@router.post("/auth/recuperar-senha", response_model=RespostaPadrao)
async def recuperar_senha(
    email: str = Query(..., description="E-mail do usuário"),
    session: Session = Depends(get_db)
) -> RespostaPadrao:
    """
    Solicitar token para recuperação de senha (RF03)
    - Token expira em 30 minutos (RN09)
    - E-mail é enviado (versão futura)
    """
    try:
        service = UsuarioService(session)
        service.solicitar_recuperacao_senha(email)

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
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Redefinir senha com token de recuperação (RF03)
    - Token pode ser usado apenas uma vez (RN09)
    """
    try:
        if nova_senha != confirmacao_senha:
            raise HTTPException(status_code=400, detail="Senhas não conferem")

        service = UsuarioService(session)
        usuario = service.redefinir_senha(token, nova_senha)

        return RespostaPadrao(
            data=usuario,
            message="Senha redefinida com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao redefinir senha: {str(e)}")


# ==================== ENDPOINTS DE PERFIL ====================

@router.get("/perfil", response_model=RespostaPadrao[UsuarioResponse])
async def obter_perfil_endpoint(
    usuario: UsuarioResponse = Depends(obter_usuario_atual)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Obter dados do perfil do usuário logado (RF06)
    - Requer autenticação JWT
    """
    return RespostaPadrao(
        data=usuario,
        message="Perfil obtido com sucesso",
        status=200
    )


@router.put("/perfil/foto", response_model=RespostaPadrao[UsuarioResponse])
async def upload_foto_perfil(
    arquivo: UploadFile = File(...),
    usuario: UsuarioResponse = Depends(obter_usuario_atual),
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Upload de foto de perfil (RF06)
    - Formatos: JPG, PNG, GIF
    - Mínimo 200x200px (RN08)
    """
    try:
        service = UsuarioService(session)
        caminho = service.upload_foto_perfil(usuario.id, arquivo)
        usuario_atualizado = service.obter_perfil(usuario.id)

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
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Alterar senha do usuário logado (RF08)
    - Requer validação de senha atual
    """
    try:
        service = UsuarioService(session)
        usuario_atualizado = service.alterar_senha(usuario.id, requisicao)

        return RespostaPadrao(
            data=usuario_atualizado,
            message="Senha alterada com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao alterar senha: {str(e)}")


# ==================== ENDPOINTS DE ADMIN ====================

@router.get("/admin/usuarios", response_model=RespostaPadrao[ListaUsuariosResponse])
async def listar_usuarios(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(10, ge=1, le=100, description="Número de registros por página"),
    usuario_admin: UsuarioResponse = Depends(require_admin),
    session: Session = Depends(get_db)
) -> RespostaPadrao[ListaUsuariosResponse]:
    """
    Listar todos os usuários (admin only)
    - Paginado
    """
    try:
        service = UsuarioService(session)
        resultado = service.listar_usuarios_paginated(skip, limit)

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
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Ativar conta de usuário (admin only) (RF04)
    """
    try:
        service = UsuarioService(session)
        usuario = service.ativar_usuario(usuario_id)

        return RespostaPadrao(
            data=usuario,
            message=f"Usuário {usuario.nome} ativado com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ativar usuário: {str(e)}")


@router.patch("/admin/usuarios/{usuario_id}/desativar", response_model=RespostaPadrao[UsuarioResponse])
async def desativar_usuario(
    usuario_id: int,
    usuario_admin: UsuarioResponse = Depends(require_admin),
    session: Session = Depends(get_db)
) -> RespostaPadrao[UsuarioResponse]:
    """
    Desativar conta de usuário (admin only) (RF04)
    """
    try:
        service = UsuarioService(session)
        usuario = service.desativar_usuario(usuario_id)

        return RespostaPadrao(
            data=usuario,
            message=f"Usuário {usuario.nome} desativado com sucesso",
            status=200
        )
    except UsuarioException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desativar usuário: {str(e)}")
