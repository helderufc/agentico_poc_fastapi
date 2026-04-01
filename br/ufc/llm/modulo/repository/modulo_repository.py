from typing import Optional, List
from sqlalchemy.orm import Session

from br.ufc.llm.modulo.domain.modulo import Modulo


class ModuloRepository:
    """Repositório para operações de persistência de módulos"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, modulo: Modulo) -> Modulo:
        self.session.add(modulo)
        self.session.commit()
        self.session.refresh(modulo)
        return modulo

    def find_by_id(self, modulo_id: int) -> Optional[Modulo]:
        return self.session.query(Modulo).filter(Modulo.id == modulo_id).first()

    def find_by_curso(self, curso_id: int) -> List[Modulo]:
        return (
            self.session.query(Modulo)
            .filter(Modulo.curso_id == curso_id)
            .order_by(Modulo.ordem)
            .all()
        )

    def count_by_curso(self, curso_id: int) -> int:
        return self.session.query(Modulo).filter(Modulo.curso_id == curso_id).count()

    def update(self, modulo: Modulo) -> Modulo:
        self.session.merge(modulo)
        self.session.commit()
        self.session.refresh(modulo)
        return modulo

    def delete(self, modulo: Modulo) -> None:
        self.session.delete(modulo)
        self.session.commit()
