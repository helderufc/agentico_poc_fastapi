from typing import Optional, List
from sqlalchemy.orm import Session

from br.ufc.llm.aula.domain.aula import Aula


class AulaRepository:
    """Repositório para operações de persistência de aulas"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, aula: Aula) -> Aula:
        self.session.add(aula)
        self.session.commit()
        self.session.refresh(aula)
        return aula

    def find_by_id(self, aula_id: int) -> Optional[Aula]:
        return self.session.query(Aula).filter(Aula.id == aula_id).first()

    def find_by_modulo(self, modulo_id: int) -> List[Aula]:
        return (
            self.session.query(Aula)
            .filter(Aula.modulo_id == modulo_id)
            .order_by(Aula.ordem)
            .all()
        )

    def count_by_modulo(self, modulo_id: int) -> int:
        return self.session.query(Aula).filter(Aula.modulo_id == modulo_id).count()

    def update(self, aula: Aula) -> Aula:
        self.session.merge(aula)
        self.session.commit()
        self.session.refresh(aula)
        return aula

    def delete(self, aula: Aula) -> None:
        self.session.delete(aula)
        self.session.commit()
