from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.curso.domain.curso import Curso


class CursoRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, curso: Curso) -> Curso:
        self.session.add(curso)
        await self.session.commit()
        await self.session.refresh(curso)
        return curso

    async def find_by_id(self, curso_id: int) -> Optional[Curso]:
        result = await self.session.execute(select(Curso).where(Curso.id == curso_id))
        return result.scalars().first()

    async def find_by_professor(
        self,
        professor_id: int,
        status: Optional[str] = None,
        q: Optional[str] = None
    ) -> Tuple[List[Curso], int]:
        stmt = select(Curso).where(Curso.professor_id == professor_id)

        if status:
            stmt = stmt.where(Curso.status == status)

        if q:
            termo = f"%{q}%"
            stmt = stmt.where(
                or_(
                    func.lower(Curso.titulo).like(func.lower(termo)),
                    func.lower(Curso.categoria).like(func.lower(termo))
                )
            )

        result = await self.session.execute(stmt)
        cursos = list(result.scalars().all())
        return cursos, len(cursos)

    async def update(self, curso: Curso) -> Curso:
        curso = await self.session.merge(curso)
        await self.session.commit()
        await self.session.refresh(curso)
        return curso

    async def delete(self, curso: Curso) -> None:
        await self.session.delete(curso)
        await self.session.commit()
