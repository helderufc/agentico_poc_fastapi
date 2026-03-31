from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Modulo(Base):
    """Modelo de módulo dentro de um curso"""
    __tablename__ = "modulos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)  # Módulo 01, Módulo 02, etc
    ordem = Column(Integer, nullable=False)
    capa = Column(String(500), nullable=True)
    curso_id = Column(Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    curso = relationship("Curso", back_populates="modulos")
    aulas = relationship("Aula", back_populates="modulo", cascade="all, delete-orphan")
    prova = relationship("Prova", back_populates="modulo", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return f"<Modulo(id={self.id}, nome={self.nome}, ordem={self.ordem})>"
