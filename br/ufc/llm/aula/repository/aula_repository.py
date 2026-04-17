from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.aula.domain.aula import Aula


class AulaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, aula: Aula) -> Aula:
        self.session.add(aula)
        await self.session.commit()
        await self.session.refresh(aula)
        return aula

    async def find_by_id(self, aula_id: int) -> Optional[Aula]:
        result = await self.session.execute(select(Aula).where(Aula.id == aula_id))
        return result.scalars().first()

    async def find_by_modulo(self, modulo_id: int) -> List[Aula]:
        result = await self.session.execute(
            select(Aula).where(Aula.modulo_id == modulo_id).order_by(Aula.ordem)
        )
        return list(result.scalars().all())

    async def count_by_modulo(self, modulo_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Aula).where(Aula.modulo_id == modulo_id)
        )
        return result.scalar()

    async def update(self, aula: Aula) -> Aula:
        aula = await self.session.merge(aula)
        await self.session.commit()
        await self.session.refresh(aula)
        return aula

    async def delete(self, aula: Aula) -> None:
        await self.session.delete(aula)
        await self.session.commit()
