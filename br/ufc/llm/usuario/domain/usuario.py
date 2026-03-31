from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Usuario(Base):
    """Modelo de usuário do sistema"""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha = Column(String(255), nullable=False)
    perfil = Column(String(20), nullable=False)  # PROFESSOR | ALUNO | ADMIN
    status = Column(String(10), nullable=False, default="INATIVO")  # ATIVO | INATIVO
    foto_perfil = Column(String(500), nullable=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    tokens_recuperacao = relationship(
        "TokenRecuperacaoSenha",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
    cursos = relationship("Curso", back_populates="professor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome={self.nome}, email={self.email}, perfil={self.perfil})>"


class TokenRecuperacaoSenha(Base):
    """Token para recuperação de senha"""
    __tablename__ = "tokens_recuperacao_senha"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expiracao = Column(DateTime, nullable=False)
    usado = Column(Boolean, nullable=False, default=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="tokens_recuperacao")

    def __repr__(self):
        return f"<TokenRecuperacaoSenha(id={self.id}, usuario_id={self.usuario_id}, usado={self.usado})>"
