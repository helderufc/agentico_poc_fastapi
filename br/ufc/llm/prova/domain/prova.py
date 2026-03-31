from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Prova(Base):
    """Modelo de prova vinculada a um módulo"""
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, index=True)
    modulo_id = Column(Integer, ForeignKey("modulos.id", ondelete="CASCADE"), nullable=False, unique=True)
    mostrar_respostas_erradas = Column(Boolean, nullable=False, default=False)
    mostrar_respostas_corretas = Column(Boolean, nullable=False, default=False)
    mostrar_valores = Column(Boolean, nullable=False, default=False)

    # Relacionamentos
    modulo = relationship("Modulo", back_populates="prova")
    perguntas = relationship("Pergunta", back_populates="prova", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Prova(id={self.id}, modulo_id={self.modulo_id})>"


class Pergunta(Base):
    """Modelo de pergunta dentro de uma prova"""
    __tablename__ = "perguntas"

    id = Column(Integer, primary_key=True, index=True)
    enunciado = Column(String(2000), nullable=False)
    pontos = Column(Integer, nullable=False, default=1)
    ordem = Column(Integer, nullable=False)
    prova_id = Column(Integer, ForeignKey("provas.id", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    prova = relationship("Prova", back_populates="perguntas")
    alternativas = relationship("Alternativa", back_populates="pergunta", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pergunta(id={self.id}, enunciado={self.enunciado[:50]}...)>"


class Alternativa(Base):
    """Modelo de alternativa de resposta"""
    __tablename__ = "alternativas"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String(1000), nullable=False)
    correta = Column(Boolean, nullable=False, default=False)
    pergunta_id = Column(Integer, ForeignKey("perguntas.id", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    pergunta = relationship("Pergunta", back_populates="alternativas")

    def __repr__(self):
        return f"<Alternativa(id={self.id}, correta={self.correta})>"
