import os
import re
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha
from br.ufc.llm.usuario.dto.usuario_dto import (
    UsuarioCadastroRequest,
    UsuarioLoginRequest,
    UsuarioResponse,
    TokenResponse,
    AlterarSenhaRequest,
    ListaUsuariosResponse
)
from br.ufc.llm.usuario.repository.usuario_repository import (
    UsuarioRepository,
    TokenRecuperacaoRepository
)
from br.ufc.llm.usuario.exception.usuario_exception import (
    UsuarioJaExisteException,
    CredenciaisInvalidasException,
    UsuarioInativoException,
    UsuarioNaoEncontradoException,
    TokenExpiradoException,
    SenhaInvalidaException,
    AcessoNegadoException
)
from br.ufc.llm.shared.domain.seguranca import SenhaUtil, JWTUtil, TokenRecuperacaoUtil


class UsuarioService:
    """Serviço de negócio para gerenciamento de usuários"""

    def __init__(self, session: Session):
        self.session = session
        self.usuario_repository = UsuarioRepository(session)
        self.token_repository = TokenRecuperacaoRepository(session)

    # ==================== AUTENTICAÇÃO ====================

    def cadastrar_usuario(self, requisicao: UsuarioCadastroRequest) -> UsuarioResponse:
        """
        Cadastrar novo usuário no sistema (RF01)
        Status inicia como INATIVO (RN01)
        """
        # Validar se CPF já existe
        if self.usuario_repository.find_by_cpf(requisicao.cpf):
            raise UsuarioJaExisteException("CPF")

        # Validar se e-mail já existe
        if self.usuario_repository.find_by_email(requisicao.email):
            raise UsuarioJaExisteException("e-mail")

        # Validar CPF (formato básico)
        if not self._validar_cpf(requisicao.cpf):
            raise ValueError("CPF em formato inválido")

        # Hash da senha
        senha_hash = SenhaUtil.hash_senha(requisicao.senha)

        # Criar usuário com status INATIVO (RN01)
        novo_usuario = Usuario(
            nome=requisicao.nome,
            cpf=requisicao.cpf,
            email=requisicao.email,
            senha=senha_hash,
            perfil=requisicao.perfil,
            status="INATIVO"  # Sempre inicia inativo
        )

        usuario_criado = self.usuario_repository.create(novo_usuario)
        return UsuarioResponse.model_validate(usuario_criado)

    def login(self, requisicao: UsuarioLoginRequest) -> TokenResponse:
        """
        Autenticar usuário e gerar tokens JWT (RF02)
        Valida status ATIVO (RN01)
        """
        # Buscar usuário por e-mail ou nome
        usuario = self.usuario_repository.find_by_email_ou_nome(requisicao.email_ou_usuario)

        if not usuario:
            raise CredenciaisInvalidasException()

        # Validar senha
        if not SenhaUtil.validar_senha(requisicao.senha, usuario.senha):
            raise CredenciaisInvalidasException()

        # Validar status (RN01)
        if usuario.status != "ATIVO":
            raise UsuarioInativoException()

        # Gerar tokens
        tokens = JWTUtil.gerar_tokens(
            usuario_id=usuario.id,
            email=usuario.email,
            perfil=usuario.perfil
        )

        return TokenResponse(**tokens)

    def refresh_token(self, refresh_token_string: str) -> TokenResponse:
        """
        Renovar access token usando refresh token
        """
        try:
            payload = JWTUtil.validar_token(refresh_token_string, tipo_esperado="refresh")
        except Exception:
            raise TokenExpiradoException()

        usuario_id = payload.get("sub")
        usuario = self.usuario_repository.find_by_id(usuario_id)

        if not usuario or usuario.status != "ATIVO":
            raise UsuarioInativoException()

        # Gerar novo par de tokens
        tokens = JWTUtil.gerar_tokens(
            usuario_id=usuario.id,
            email=usuario.email,
            perfil=usuario.perfil
        )

        return TokenResponse(**tokens)

    # ==================== RECUPERAÇÃO DE SENHA ====================

    def solicitar_recuperacao_senha(self, email: str) -> None:
        """
        Solicitar token para recuperação de senha (RF03)
        Token expira em 30 min (RN09)
        """
        usuario = self.usuario_repository.find_by_email(email)

        if not usuario:
            # Não revelar se usuário existe ou não (segurança)
            return None

        # Limpar tokens antigos
        self.token_repository.delete_expired(usuario.id)

        # Gerar novo token
        token_string = TokenRecuperacaoUtil.gerar_token()
        expiracao = TokenRecuperacaoUtil.calcular_expiracao()

        token_recuperacao = TokenRecuperacaoSenha(
            token=token_string,
            expiracao=expiracao,
            usado=False,
            usuario_id=usuario.id
        )

        self.token_repository.create(token_recuperacao)

        # TODO: Enviar e-mail com token (RF03)
        # send_email(email, token_string)

        return None

    def redefinir_senha(self, token_string: str, nova_senha: str) -> UsuarioResponse:
        """
        Redefinir senha com token de recuperação (RF03)
        Token pode ser usado apenas uma vez (RN09)
        """
        token = self.token_repository.find_by_token(token_string)

        if not token:
            raise TokenExpiradoException()

        # Validar expiração (RN09)
        if TokenRecuperacaoUtil.token_expirado(token.expiracao):
            raise TokenExpiradoException()

        # Validar se já foi usado (RN09)
        if token.usado:
            raise TokenExpiradoException()

        # Buscar usuário
        usuario = self.usuario_repository.find_by_id(token.usuario_id)
        if not usuario:
            raise UsuarioNaoEncontradoException()

        # Atualizar senha
        usuario.senha = SenhaUtil.hash_senha(nova_senha)
        usuario_atualizado = self.usuario_repository.update(usuario)

        # Marcar token como usado (RN09)
        self.token_repository.mark_as_used(token.id)

        return UsuarioResponse.model_validate(usuario_atualizado)

    # ==================== PERFIL ====================

    def obter_perfil(self, usuario_id: int) -> UsuarioResponse:
        """
        Obter dados do perfil do usuário logado (RF06)
        """
        usuario = self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        return UsuarioResponse.model_validate(usuario)

    def alterar_senha(self, usuario_id: int, requisicao: AlterarSenhaRequest) -> UsuarioResponse:
        """
        Alterar senha do usuário logado (RF08)
        Requer validação de senha atual
        """
        usuario = self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        # Validar senha atual
        if not SenhaUtil.validar_senha(requisicao.senha_atual, usuario.senha):
            raise SenhaInvalidaException()

        # Validar confirmação
        if requisicao.nova_senha != requisicao.confirmacao_nova_senha:
            raise ValueError("As senhas não conferem")

        # Hash da nova senha
        usuario.senha = SenhaUtil.hash_senha(requisicao.nova_senha)
        usuario_atualizado = self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    def upload_foto_perfil(self, usuario_id: int, arquivo: UploadFile) -> str:
        """
        Upload de foto de perfil (RF06)
        Validações: JPG, PNG, GIF; mínimo 200x200px (RN08)
        """
        from PIL import Image
        import mimetypes

        usuario = self.usuario_repository.find_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontradoException()

        # Validar tipo MIME
        mime_type, _ = mimetypes.guess_type(arquivo.filename)
        if mime_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise ValueError("Formato de imagem não suportado. Use JPG, PNG ou GIF")

        # Ler arquivo em memória
        conteudo = arquivo.file.read()

        # Validar dimensões
        try:
            imagem = Image.open(arquivo.file)
            arquivo.file.seek(0)  # Reset file pointer
            width, height = imagem.size

            if width < 200 or height < 200:
                raise ValueError("Imagem deve ter no mínimo 200x200 pixels")
        except Exception as e:
            raise ValueError(f"Erro ao validar imagem: {str(e)}")

        # Criar diretório de uploads se não existir
        diretorio_upload = f"uploads/fotos/{usuario_id}"
        os.makedirs(diretorio_upload, exist_ok=True)

        # Salvar arquivo
        extensao = arquivo.filename.split(".")[-1].lower()
        timestamp = datetime.utcnow().timestamp()
        nome_arquivo = f"{int(timestamp)}.{extensao}"
        caminho_arquivo = os.path.join(diretorio_upload, nome_arquivo)

        with open(caminho_arquivo, "wb") as f:
            f.write(conteudo)

        # Atualizar usuário
        usuario.foto_perfil = caminho_arquivo
        self.usuario_repository.update(usuario)

        return caminho_arquivo

    # ==================== ADMIN ====================

    def ativar_usuario(self, usuario_id: int) -> UsuarioResponse:
        """
        Ativar conta de usuário (RF04)
        """
        usuario = self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        usuario.status = "ATIVO"
        usuario_atualizado = self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    def desativar_usuario(self, usuario_id: int) -> UsuarioResponse:
        """
        Desativar conta de usuário (RF04)
        """
        usuario = self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        usuario.status = "INATIVO"
        usuario_atualizado = self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    def listar_usuarios_paginated(self, skip: int = 0, limit: int = 10) -> ListaUsuariosResponse:
        """
        Listar todos os usuários com paginação (admin)
        """
        usuarios, total = self.usuario_repository.list_all_paginated(skip, limit)
        usuarios_response = [UsuarioResponse.model_validate(u) for u in usuarios]

        pagina = (skip // limit) + 1 if limit > 0 else 1

        return ListaUsuariosResponse(
            usuarios=usuarios_response,
            total=total,
            pagina=pagina,
            tamanho=limit
        )

    # ==================== UTILIDADES ====================

    @staticmethod
    def _validar_cpf(cpf: str) -> bool:
        """Validação básica de formato de CPF"""
        return bool(re.match(r"^\d{11}$", cpf))
