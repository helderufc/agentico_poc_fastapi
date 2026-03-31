from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


class UsuarioCadastroRequest(BaseModel):
    """DTO para cadastro de novo usuário"""
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo do usuário")
    cpf: str = Field(..., regex=r"^\d{11}$", description="CPF sem formatação (11 dígitos)")
    email: EmailStr = Field(..., description="E-mail único do usuário")
    senha: str = Field(..., min_length=8, description="Senha com mínimo 8 caracteres")
    perfil: Literal["PROFESSOR", "ALUNO"] = Field(..., description="Perfil do usuário")


class UsuarioLoginRequest(BaseModel):
    """DTO para login"""
    email_ou_usuario: str = Field(..., description="E-mail ou nome de usuário")
    senha: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    """DTO de resposta com tokens JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tempo de expiração em segundos")


class UsuarioResponse(BaseModel):
    """DTO de resposta com dados do usuário (sem senha)"""
    id: int
    nome: str
    cpf: str
    email: str
    perfil: str
    status: str
    foto_perfil: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class RecuperacaoSenhaRequest(BaseModel):
    """DTO para solicitar recuperação de senha"""
    email: EmailStr = Field(..., description="E-mail cadastrado no sistema")


class RedefinirSenhaRequest(BaseModel):
    """DTO para redefinir senha com token"""
    token: str = Field(..., description="Token de recuperação enviado por e-mail")
    nova_senha: str = Field(..., min_length=8, description="Nova senha com mínimo 8 caracteres")
    confirmacao_senha: str = Field(..., description="Confirmação da nova senha")


class AlterarSenhaRequest(BaseModel):
    """DTO para alterar senha do usuário logado"""
    senha_atual: str = Field(..., description="Senha atual do usuário")
    nova_senha: str = Field(..., min_length=8, description="Nova senha com mínimo 8 caracteres")
    confirmacao_nova_senha: str = Field(..., description="Confirmação da nova senha")


class RefreshTokenRequest(BaseModel):
    """DTO para renovar access token"""
    refresh_token: str = Field(..., description="Refresh token válido")


class ListaUsuariosResponse(BaseModel):
    """DTO de resposta para listagem paginada de usuários"""
    usuarios: list[UsuarioResponse]
    total: int
    pagina: int
    tamanho: int
