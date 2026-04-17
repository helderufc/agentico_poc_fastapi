from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva
from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.modulo.domain.modulo import Modulo
from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.prova.domain.prova import Prova


class MatriculaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_aluno_and_curso(self, aluno_id: int, curso_id: int) -> Optional[Matricula]:
        result = await self.session.execute(
            select(Matricula).where(Matricula.aluno_id == aluno_id, Matricula.curso_id == curso_id)
        )
        return result.scalars().first()

    async def find_by_aluno(self, aluno_id: int) -> List[Matricula]:
        result = await self.session.execute(select(Matricula).where(Matricula.aluno_id == aluno_id))
        return list(result.scalars().all())

    async def create(self, matricula: Matricula) -> Matricula:
        self.session.add(matricula)
        await self.session.commit()
        await self.session.refresh(matricula)
        return matricula

    async def find_cursos_publicados(self, q: Optional[str] = None) -> List[Curso]:
        stmt = select(Curso).where(Curso.status == "PUBLICADO")
        if q:
            termo = f"%{q}%"
            stmt = stmt.where(func.lower(Curso.titulo).like(func.lower(termo)))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_curso_publicado_by_id(self, curso_id: int) -> Optional[Curso]:
        result = await self.session.execute(
            select(Curso).where(Curso.id == curso_id, Curso.status == "PUBLICADO")
        )
        return result.scalars().first()

    async def find_modulos_by_curso(self, curso_id: int) -> List[Modulo]:
        result = await self.session.execute(
            select(Modulo).where(Modulo.curso_id == curso_id).order_by(Modulo.ordem)
        )
        return list(result.scalars().all())

    async def find_aulas_by_modulo(self, modulo_id: int) -> List[Aula]:
        result = await self.session.execute(
            select(Aula).where(Aula.modulo_id == modulo_id).order_by(Aula.ordem)
        )
        return list(result.scalars().all())

    async def find_aula_by_id(self, aula_id: int) -> Optional[Aula]:
        result = await self.session.execute(select(Aula).where(Aula.id == aula_id))
        return result.scalars().first()

    async def find_prova_by_modulo(self, modulo_id: int) -> Optional[Prova]:
        result = await self.session.execute(select(Prova).where(Prova.modulo_id == modulo_id))
        return result.scalars().first()

    async def find_prova_by_id(self, prova_id: int) -> Optional[Prova]:
        result = await self.session.execute(select(Prova).where(Prova.id == prova_id))
        return result.scalars().first()

    async def find_respostas_by_aluno_and_prova(self, aluno_id: int, prova_id: int) -> List[RespostaProva]:
        result = await self.session.execute(
            select(RespostaProva).where(
                RespostaProva.aluno_id == aluno_id,
                RespostaProva.prova_id == prova_id
            )
        )
        return list(result.scalars().all())

    async def find_resposta_by_aluno_and_pergunta(self, aluno_id: int, pergunta_id: int) -> Optional[RespostaProva]:
        result = await self.session.execute(
            select(RespostaProva).where(
                RespostaProva.aluno_id == aluno_id,
                RespostaProva.pergunta_id == pergunta_id
            )
        )
        return result.scalars().first()

    async def create_resposta(self, resposta: RespostaProva) -> RespostaProva:
        self.session.add(resposta)
        await self.session.commit()
        await self.session.refresh(resposta)
        return resposta
