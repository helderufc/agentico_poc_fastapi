from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa


class ProvaRepository:
    """Repositório para operações de persistência de provas"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, prova: Prova) -> Prova:
        self.session.add(prova)
        self.session.commit()
        self.session.refresh(prova)
        return prova

    def find_by_id(self, prova_id: int) -> Optional[Prova]:
        return self.session.query(Prova).filter(Prova.id == prova_id).first()

    def find_by_modulo(self, modulo_id: int) -> Optional[Prova]:
        return self.session.query(Prova).filter(Prova.modulo_id == modulo_id).first()

    def update(self, prova: Prova) -> Prova:
        self.session.merge(prova)
        self.session.commit()
        self.session.refresh(prova)
        return prova

    def delete(self, prova: Prova) -> None:
        self.session.delete(prova)
        self.session.commit()


class PerguntaRepository:
    """Repositório para operações de persistência de perguntas"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, pergunta: Pergunta) -> Pergunta:
        self.session.add(pergunta)
        self.session.commit()
        self.session.refresh(pergunta)
        return pergunta

    def find_by_id(self, pergunta_id: int) -> Optional[Pergunta]:
        return self.session.query(Pergunta).filter(Pergunta.id == pergunta_id).first()

    def find_by_prova(self, prova_id: int) -> List[Pergunta]:
        return (
            self.session.query(Pergunta)
            .filter(Pergunta.prova_id == prova_id)
            .order_by(Pergunta.ordem)
            .all()
        )

    def count_by_prova(self, prova_id: int) -> int:
        return self.session.query(Pergunta).filter(Pergunta.prova_id == prova_id).count()

    def update(self, pergunta: Pergunta) -> Pergunta:
        self.session.merge(pergunta)
        self.session.commit()
        self.session.refresh(pergunta)
        return pergunta

    def delete(self, pergunta: Pergunta) -> None:
        self.session.delete(pergunta)
        self.session.commit()

    def delete_alternativas(self, pergunta_id: int) -> None:
        self.session.query(Alternativa).filter(Alternativa.pergunta_id == pergunta_id).delete()
        self.session.commit()

    def count_respostas_por_alternativa(self, prova_id: int) -> Dict[int, int]:
        """Retorna {alternativa_id: total_respostas} para toda a prova"""
        from br.ufc.llm.matricula.domain.matricula import RespostaProva
        rows = (
            self.session.query(RespostaProva.alternativa_id, func.count(RespostaProva.id))
            .filter(RespostaProva.prova_id == prova_id)
            .group_by(RespostaProva.alternativa_id)
            .all()
        )
        return {alt_id: total for alt_id, total in rows}

    def count_respondentes(self, prova_id: int) -> int:
        """Total de alunos distintos que responderam a prova"""
        from br.ufc.llm.matricula.domain.matricula import RespostaProva
        return (
            self.session.query(func.count(func.distinct(RespostaProva.aluno_id)))
            .filter(RespostaProva.prova_id == prova_id)
            .scalar()
        ) or 0
