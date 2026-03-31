from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Aula(Base):
    """Modelo de aula dentro de um módulo"""
    __tablename__ = "aulas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    ordem = Column(Integer, nullable=False)
    arquivo = Column(String(500), nullable=True)  # Caminho do PDF ou vídeo
    tipo_arquivo = Column(String(10), nullable=True)  # PDF | VIDEO
    conteudo_ck_editor = Column(Text, nullable=True)  # HTML digitado
    conteudo_gerado = Column(Text, nullable=True)  # HTML gerado pela IA
    modulo_id = Column(Integer, ForeignKey("modulos.id", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    modulo = relationship("Modulo", back_populates="aulas")

    def __repr__(self):
        return f"<Aula(id={self.id}, nome={self.nome}, ordem={self.ordem})>"
