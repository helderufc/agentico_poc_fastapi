from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Curso(Base):
    """Modelo de curso"""
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    carga_horaria = Column(String(20), nullable=False)  # ex: "30h"
    capa = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="RASCUNHO")  # RASCUNHO | PUBLICADO | ARQUIVADO
    requer_endereco = Column(Boolean, nullable=False, default=False)
    requer_genero = Column(Boolean, nullable=False, default=False)
    requer_idade = Column(Boolean, nullable=False, default=False)
    professor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    professor = relationship("Usuario", back_populates="cursos")
    modulos = relationship("Modulo", back_populates="curso", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Curso(id={self.id}, titulo={self.titulo}, status={self.status})>"
