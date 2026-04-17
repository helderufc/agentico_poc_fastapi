from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha
from br.ufc.llm.usuario.exception.usuario_exception import UsuarioNaoEncontradoException


class UsuarioRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario

    async def find_by_id(self, usuario_id: int) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.id == int(usuario_id)))
        return result.scalars().first()

    async def find_by_cpf(self, cpf: str) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.cpf == cpf))
        return result.scalars().first()

    async def find_by_email(self, email: str) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.email == email))
        return result.scalars().first()

    async def find_by_email_ou_nome(self, email_ou_nome: str) -> Optional[Usuario]:
        result = await self.session.execute(
            select(Usuario).where(
                (Usuario.email == email_ou_nome) | (Usuario.nome == email_ou_nome)
            )
        )
        return result.scalars().first()

    async def update(self, usuario: Usuario) -> Usuario:
        usuario = await self.session.merge(usuario)
        await self.session.commit()
        return usuario

    async def delete(self, usuario_id: int) -> bool:
        usuario = await self.find_by_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoException()
        await self.session.delete(usuario)
        await self.session.commit()
        return True

    async def list_all_paginated(self, skip: int = 0, limit: int = 10) -> tuple[List[Usuario], int]:
        total_result = await self.session.execute(select(func.count()).select_from(Usuario))
        total = total_result.scalar()
        result = await self.session.execute(select(Usuario).offset(skip).limit(limit))
        usuarios = result.scalars().all()
        return list(usuarios), total


class TokenRecuperacaoRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: TokenRecuperacaoSenha) -> TokenRecuperacaoSenha:
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def find_by_token(self, token_string: str) -> Optional[TokenRecuperacaoSenha]:
        result = await self.session.execute(
            select(TokenRecuperacaoSenha).where(TokenRecuperacaoSenha.token == token_string)
        )
        return result.scalars().first()

    async def find_by_usuario_id(self, usuario_id: int) -> List[TokenRecuperacaoSenha]:
        result = await self.session.execute(
            select(TokenRecuperacaoSenha).where(TokenRecuperacaoSenha.usuario_id == usuario_id)
        )
        return list(result.scalars().all())

    async def mark_as_used(self, token_id: int) -> Optional[TokenRecuperacaoSenha]:
        result = await self.session.execute(
            select(TokenRecuperacaoSenha).where(TokenRecuperacaoSenha.id == token_id)
        )
        token = result.scalars().first()
        if token:
            token.usado = True
            token = await self.session.merge(token)
            await self.session.commit()
        return token

    async def delete_expired(self, usuario_id: int) -> int:
        result = await self.session.execute(
            delete(TokenRecuperacaoSenha).where(
                TokenRecuperacaoSenha.usuario_id == usuario_id,
                TokenRecuperacaoSenha.expiracao < datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount
