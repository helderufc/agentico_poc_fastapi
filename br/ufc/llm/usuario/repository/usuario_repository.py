from typing import Optional, List
from sqlalchemy.orm import Session
from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha
from br.ufc.llm.usuario.exception.usuario_exception import UsuarioNaoEncontradoException


class UsuarioRepository:
    """Repositório para operações de persistência de usuários"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, usuario: Usuario) -> Usuario:
        """Criar novo usuário"""
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def find_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """Buscar usuário por ID"""
        return self.session.query(Usuario).filter(Usuario.id == usuario_id).first()

    def find_by_cpf(self, cpf: str) -> Optional[Usuario]:
        """Buscar usuário por CPF"""
        return self.session.query(Usuario).filter(Usuario.cpf == cpf).first()

    def find_by_email(self, email: str) -> Optional[Usuario]:
        """Buscar usuário por e-mail"""
        return self.session.query(Usuario).filter(Usuario.email == email).first()

    def find_by_email_ou_nome(self, email_ou_nome: str) -> Optional[Usuario]:
        """Buscar usuário por e-mail ou nome"""
        return self.session.query(Usuario).filter(
            (Usuario.email == email_ou_nome) | (Usuario.nome == email_ou_nome)
        ).first()

    def update(self, usuario: Usuario) -> Usuario:
        """Atualizar usuário"""
        self.session.merge(usuario)
        self.session.commit()
        return usuario

    def delete(self, usuario_id: int) -> bool:
        """Deletar usuário por ID"""
        usuario = self.find_by_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoException()
        self.session.delete(usuario)
        self.session.commit()
        return True

    def list_all_paginated(self, skip: int = 0, limit: int = 10) -> tuple[List[Usuario], int]:
        """Listar todos os usuários com paginação"""
        total = self.session.query(Usuario).count()
        usuarios = self.session.query(Usuario).offset(skip).limit(limit).all()
        return usuarios, total


class TokenRecuperacaoRepository:
    """Repositório para operações de tokens de recuperação de senha"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, token: TokenRecuperacaoSenha) -> TokenRecuperacaoSenha:
        """Criar novo token de recuperação"""
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def find_by_token(self, token_string: str) -> Optional[TokenRecuperacaoSenha]:
        """Buscar token pelo string"""
        return self.session.query(TokenRecuperacaoSenha).filter(
            TokenRecuperacaoSenha.token == token_string
        ).first()

    def find_by_usuario_id(self, usuario_id: int) -> List[TokenRecuperacaoSenha]:
        """Buscar todos os tokens de um usuário"""
        return self.session.query(TokenRecuperacaoSenha).filter(
            TokenRecuperacaoSenha.usuario_id == usuario_id
        ).all()

    def mark_as_used(self, token_id: int) -> TokenRecuperacaoSenha:
        """Marcar token como usado"""
        token = self.session.query(TokenRecuperacaoSenha).filter(
            TokenRecuperacaoSenha.id == token_id
        ).first()
        if token:
            token.usado = True
            self.session.merge(token)
            self.session.commit()
        return token

    def delete_expired(self, usuario_id: int) -> int:
        """Deletar tokens expirados de um usuário"""
        from datetime import datetime
        deleted = self.session.query(TokenRecuperacaoSenha).filter(
            TokenRecuperacaoSenha.usuario_id == usuario_id,
            TokenRecuperacaoSenha.expiracao < datetime.utcnow()
        ).delete()
        self.session.commit()
        return deleted
