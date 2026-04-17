from typing import Optional, List, Dict
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa


class ProvaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, prova: Prova) -> Prova:
        self.session.add(prova)
        await self.session.commit()
        await self.session.refresh(prova)
        return prova

    async def find_by_id(self, prova_id: int) -> Optional[Prova]:
        result = await self.session.execute(select(Prova).where(Prova.id == prova_id))
        return result.scalars().first()

    async def find_by_modulo(self, modulo_id: int) -> Optional[Prova]:
        result = await self.session.execute(select(Prova).where(Prova.modulo_id == modulo_id))
        return result.scalars().first()

    async def update(self, prova: Prova) -> Prova:
        prova = await self.session.merge(prova)
        await self.session.commit()
        await self.session.refresh(prova)
        return prova

    async def delete(self, prova: Prova) -> None:
        await self.session.delete(prova)
        await self.session.commit()


class PerguntaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, pergunta: Pergunta) -> Pergunta:
        self.session.add(pergunta)
        await self.session.commit()
        await self.session.refresh(pergunta)
        return pergunta

    async def find_by_id(self, pergunta_id: int) -> Optional[Pergunta]:
        result = await self.session.execute(select(Pergunta).where(Pergunta.id == pergunta_id))
        return result.scalars().first()

    async def find_by_prova(self, prova_id: int) -> List[Pergunta]:
        result = await self.session.execute(
            select(Pergunta).where(Pergunta.prova_id == prova_id).order_by(Pergunta.ordem)
        )
        return list(result.scalars().all())

    async def count_by_prova(self, prova_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Pergunta).where(Pergunta.prova_id == prova_id)
        )
        return result.scalar()

    async def update(self, pergunta: Pergunta) -> Pergunta:
        pergunta = await self.session.merge(pergunta)
        await self.session.commit()
        await self.session.refresh(pergunta)
        return pergunta

    async def delete(self, pergunta: Pergunta) -> None:
        await self.session.delete(pergunta)
        await self.session.commit()

    async def delete_alternativas(self, pergunta_id: int) -> None:
        await self.session.execute(delete(Alternativa).where(Alternativa.pergunta_id == pergunta_id))
        await self.session.commit()

    async def count_respostas_por_alternativa(self, prova_id: int) -> Dict[int, int]:
        from br.ufc.llm.matricula.domain.matricula import RespostaProva
        result = await self.session.execute(
            select(RespostaProva.alternativa_id, func.count(RespostaProva.id))
            .where(RespostaProva.prova_id == prova_id)
            .group_by(RespostaProva.alternativa_id)
        )
        return {alt_id: total for alt_id, total in result.all()}

    async def count_respondentes(self, prova_id: int) -> int:
        from br.ufc.llm.matricula.domain.matricula import RespostaProva
        result = await self.session.execute(
            select(func.count(func.distinct(RespostaProva.aluno_id)))
            .where(RespostaProva.prova_id == prova_id)
        )
        return result.scalar() or 0
