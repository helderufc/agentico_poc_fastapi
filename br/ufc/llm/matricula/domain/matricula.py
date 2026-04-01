from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Matricula(Base):
    """Matrícula de aluno em curso"""
    __tablename__ = "matriculas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    endereco = Column(String(500), nullable=True)
    genero = Column(String(20), nullable=True)
    idade = Column(Integer, nullable=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("aluno_id", "curso_id", name="uq_matricula_aluno_curso"),
    )

    # Relacionamentos
    aluno = relationship("Usuario", foreign_keys=[aluno_id])
    curso = relationship("Curso", foreign_keys=[curso_id])

    def __repr__(self):
        return f"<Matricula(id={self.id}, aluno_id={self.aluno_id}, curso_id={self.curso_id})>"


class RespostaProva(Base):
    """Resposta de aluno a uma pergunta de prova"""
    __tablename__ = "respostas_prova"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False)
    pergunta_id = Column(Integer, ForeignKey("perguntas.id"), nullable=False)
    alternativa_id = Column(Integer, ForeignKey("alternativas.id"), nullable=False)
    respondido_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("aluno_id", "pergunta_id", name="uq_resposta_aluno_pergunta"),
    )

    # Relacionamentos
    aluno = relationship("Usuario", foreign_keys=[aluno_id])
    prova = relationship("Prova", foreign_keys=[prova_id])
    pergunta = relationship("Pergunta", foreign_keys=[pergunta_id])
    alternativa = relationship("Alternativa", foreign_keys=[alternativa_id])

    def __repr__(self):
        return f"<RespostaProva(id={self.id}, aluno_id={self.aluno_id}, pergunta_id={self.pergunta_id})>"
