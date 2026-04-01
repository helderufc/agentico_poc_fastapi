from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from br.ufc.llm.curso.domain.curso import Curso


class CursoRepository:
    """Repositório para operações de persistência de cursos"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, curso: Curso) -> Curso:
        self.session.add(curso)
        self.session.commit()
        self.session.refresh(curso)
        return curso

    def find_by_id(self, curso_id: int) -> Optional[Curso]:
        return self.session.query(Curso).filter(Curso.id == curso_id).first()

    def find_by_professor(
        self,
        professor_id: int,
        status: Optional[str] = None,
        q: Optional[str] = None
    ) -> Tuple[List[Curso], int]:
        query = self.session.query(Curso).filter(Curso.professor_id == professor_id)

        if status:
            query = query.filter(Curso.status == status)

        if q:
            termo = f"%{q}%"
            query = query.filter(
                or_(
                    func.lower(Curso.titulo).like(func.lower(termo)),
                    func.lower(Curso.categoria).like(func.lower(termo))
                )
            )

        total = query.count()
        cursos = query.all()
        return cursos, total

    def update(self, curso: Curso) -> Curso:
        self.session.merge(curso)
        self.session.commit()
        self.session.refresh(curso)
        return curso

    def delete(self, curso: Curso) -> None:
        self.session.delete(curso)
        self.session.commit()
