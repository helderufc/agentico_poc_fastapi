import asyncio
import io
import os
import re
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
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


def _salvar_arquivo(caminho: str, conteudo: bytes) -> None:
    with open(caminho, "wb") as f:
        f.write(conteudo)


class UsuarioService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.usuario_repository = UsuarioRepository(session)
        self.token_repository = TokenRecuperacaoRepository(session)

    async def cadastrar_usuario(self, requisicao: UsuarioCadastroRequest) -> UsuarioResponse:
        if await self.usuario_repository.find_by_cpf(requisicao.cpf):
            raise UsuarioJaExisteException("CPF")

        if await self.usuario_repository.find_by_email(requisicao.email):
            raise UsuarioJaExisteException("e-mail")

        if not self._validar_cpf(requisicao.cpf):
            raise ValueError("CPF em formato inválido")

        senha_hash = SenhaUtil.hash_senha(requisicao.senha)

        novo_usuario = Usuario(
            nome=requisicao.nome,
            cpf=requisicao.cpf,
            email=requisicao.email,
            senha=senha_hash,
            perfil=requisicao.perfil,
            status="INATIVO"
        )

        usuario_criado = await self.usuario_repository.create(novo_usuario)
        return UsuarioResponse.model_validate(usuario_criado)

    async def login(self, requisicao: UsuarioLoginRequest) -> TokenResponse:
        usuario = await self.usuario_repository.find_by_email_ou_nome(requisicao.email_ou_usuario)

        if not usuario:
            raise CredenciaisInvalidasException()

        if not SenhaUtil.validar_senha(requisicao.senha, usuario.senha):
            raise CredenciaisInvalidasException()

        if usuario.status != "ATIVO":
            raise UsuarioInativoException()

        tokens = JWTUtil.gerar_tokens(
            usuario_id=usuario.id,
            email=usuario.email,
            perfil=usuario.perfil
        )

        return TokenResponse(**tokens)

    async def refresh_token(self, refresh_token_string: str) -> TokenResponse:
        try:
            payload = JWTUtil.validar_token(refresh_token_string, tipo_esperado="refresh")
        except Exception:
            raise TokenExpiradoException()

        usuario_id = payload.get("sub")
        usuario = await self.usuario_repository.find_by_id(usuario_id)

        if not usuario or usuario.status != "ATIVO":
            raise UsuarioInativoException()

        tokens = JWTUtil.gerar_tokens(
            usuario_id=usuario.id,
            email=usuario.email,
            perfil=usuario.perfil
        )

        return TokenResponse(**tokens)

    async def solicitar_recuperacao_senha(self, email: str) -> None:
        usuario = await self.usuario_repository.find_by_email(email)

        if not usuario:
            return None

        await self.token_repository.delete_expired(usuario.id)

        token_string = TokenRecuperacaoUtil.gerar_token()
        expiracao = TokenRecuperacaoUtil.calcular_expiracao()

        token_recuperacao = TokenRecuperacaoSenha(
            token=token_string,
            expiracao=expiracao,
            usado=False,
            usuario_id=usuario.id
        )

        await self.token_repository.create(token_recuperacao)
        return None

    async def redefinir_senha(self, token_string: str, nova_senha: str) -> UsuarioResponse:
        token = await self.token_repository.find_by_token(token_string)

        if not token:
            raise TokenExpiradoException()

        if TokenRecuperacaoUtil.token_expirado(token.expiracao):
            raise TokenExpiradoException()

        if token.usado:
            raise TokenExpiradoException()

        usuario = await self.usuario_repository.find_by_id(token.usuario_id)
        if not usuario:
            raise UsuarioNaoEncontradoException()

        usuario.senha = SenhaUtil.hash_senha(nova_senha)
        usuario_atualizado = await self.usuario_repository.update(usuario)

        await self.token_repository.mark_as_used(token.id)

        return UsuarioResponse.model_validate(usuario_atualizado)

    async def obter_perfil(self, usuario_id: int) -> UsuarioResponse:
        usuario = await self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        return UsuarioResponse.model_validate(usuario)

    async def alterar_senha(self, usuario_id: int, requisicao: AlterarSenhaRequest) -> UsuarioResponse:
        usuario = await self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        if not SenhaUtil.validar_senha(requisicao.senha_atual, usuario.senha):
            raise SenhaInvalidaException()

        if requisicao.nova_senha != requisicao.confirmacao_nova_senha:
            raise ValueError("As senhas não conferem")

        usuario.senha = SenhaUtil.hash_senha(requisicao.nova_senha)
        usuario_atualizado = await self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    async def upload_foto_perfil(self, usuario_id: int, arquivo: UploadFile) -> str:
        from PIL import Image
        import mimetypes

        usuario = await self.usuario_repository.find_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontradoException()

        mime_type, _ = mimetypes.guess_type(arquivo.filename)
        if mime_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise ValueError("Formato de imagem não suportado. Use JPG, PNG ou GIF")

        conteudo = await arquivo.read()

        try:
            def _obter_dimensoes():
                imagem = Image.open(io.BytesIO(conteudo))
                return imagem.size
            width, height = await asyncio.to_thread(_obter_dimensoes)
            if width < 200 or height < 200:
                raise ValueError("Imagem deve ter no mínimo 200x200 pixels")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Erro ao validar imagem: {str(e)}")

        diretorio_upload = f"uploads/fotos/{usuario_id}"
        os.makedirs(diretorio_upload, exist_ok=True)

        extensao = arquivo.filename.split(".")[-1].lower()
        timestamp = datetime.utcnow().timestamp()
        nome_arquivo = f"{int(timestamp)}.{extensao}"
        caminho_arquivo = os.path.join(diretorio_upload, nome_arquivo)

        await asyncio.to_thread(_salvar_arquivo, caminho_arquivo, conteudo)

        usuario.foto_perfil = caminho_arquivo
        await self.usuario_repository.update(usuario)

        return caminho_arquivo

    async def ativar_usuario(self, usuario_id: int) -> UsuarioResponse:
        usuario = await self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        usuario.status = "ATIVO"
        usuario_atualizado = await self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    async def desativar_usuario(self, usuario_id: int) -> UsuarioResponse:
        usuario = await self.usuario_repository.find_by_id(usuario_id)

        if not usuario:
            raise UsuarioNaoEncontradoException()

        usuario.status = "INATIVO"
        usuario_atualizado = await self.usuario_repository.update(usuario)

        return UsuarioResponse.model_validate(usuario_atualizado)

    async def listar_usuarios_paginated(self, skip: int = 0, limit: int = 10) -> ListaUsuariosResponse:
        usuarios, total = await self.usuario_repository.list_all_paginated(skip, limit)
        usuarios_response = [UsuarioResponse.model_validate(u) for u in usuarios]

        pagina = (skip // limit) + 1 if limit > 0 else 1

        return ListaUsuariosResponse(
            usuarios=usuarios_response,
            total=total,
            pagina=pagina,
            tamanho=limit
        )

    @staticmethod
    def _validar_cpf(cpf: str) -> bool:
        return bool(re.match(r"^\d{11}$", cpf))
