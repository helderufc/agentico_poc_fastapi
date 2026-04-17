from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.modulo.domain.modulo import Modulo


class ModuloRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, modulo: Modulo) -> Modulo:
        self.session.add(modulo)
        await self.session.commit()
        await self.session.refresh(modulo)
        return modulo

    async def find_by_id(self, modulo_id: int) -> Optional[Modulo]:
        result = await self.session.execute(select(Modulo).where(Modulo.id == modulo_id))
        return result.scalars().first()

    async def find_by_curso(self, curso_id: int) -> List[Modulo]:
        result = await self.session.execute(
            select(Modulo).where(Modulo.curso_id == curso_id).order_by(Modulo.ordem)
        )
        return list(result.scalars().all())

    async def count_by_curso(self, curso_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Modulo).where(Modulo.curso_id == curso_id)
        )
        return result.scalar()

    async def update(self, modulo: Modulo) -> Modulo:
        modulo = await self.session.merge(modulo)
        await self.session.commit()
        await self.session.refresh(modulo)
        return modulo

    async def delete(self, modulo: Modulo) -> None:
        await self.session.delete(modulo)
        await self.session.commit()
