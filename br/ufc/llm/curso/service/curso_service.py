import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.curso.dto.curso_dto import CursoRequest, CursoResponse, ListaCursosResponse
from br.ufc.llm.curso.repository.curso_repository import CursoRepository
from br.ufc.llm.curso.exception.curso_exception import (
    CursoNaoEncontradoException,
    CursoAcessoNegadoException
)


class CursoService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CursoRepository(session)

    async def criar_curso(self, requisicao: CursoRequest, professor_id: int) -> CursoResponse:
        curso = Curso(
            titulo=requisicao.titulo,
            categoria=requisicao.categoria.upper(),
            descricao=requisicao.descricao,
            carga_horaria=requisicao.carga_horaria,
            requer_endereco=requisicao.requer_endereco,
            requer_genero=requisicao.requer_genero,
            requer_idade=requisicao.requer_idade,
            status="RASCUNHO",
            professor_id=professor_id
        )
        curso_criado = await self.repository.create(curso)
        return CursoResponse.model_validate(curso_criado)

    async def listar_cursos(
        self,
        professor_id: int,
        status: Optional[str] = None,
        q: Optional[str] = None
    ) -> ListaCursosResponse:
        cursos, total = await self.repository.find_by_professor(professor_id, status, q)
        return ListaCursosResponse(
            cursos=[CursoResponse.model_validate(c) for c in cursos],
            total=total
        )

    async def obter_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        curso = await self._obter_e_validar(curso_id, professor_id)
        return CursoResponse.model_validate(curso)

    async def editar_curso(self, curso_id: int, requisicao: CursoRequest, professor_id: int) -> CursoResponse:
        curso = await self._obter_e_validar(curso_id, professor_id)

        curso.titulo = requisicao.titulo
        curso.categoria = requisicao.categoria.upper()
        curso.descricao = requisicao.descricao
        curso.carga_horaria = requisicao.carga_horaria
        curso.requer_endereco = requisicao.requer_endereco
        curso.requer_genero = requisicao.requer_genero
        curso.requer_idade = requisicao.requer_idade

        curso_atualizado = await self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    async def deletar_curso(self, curso_id: int, professor_id: int) -> None:
        curso = await self._obter_e_validar(curso_id, professor_id)
        await self.repository.delete(curso)

    async def publicar_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        curso = await self._obter_e_validar(curso_id, professor_id)
        curso.status = "PUBLICADO"
        curso_atualizado = await self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    async def arquivar_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        curso = await self._obter_e_validar(curso_id, professor_id)
        curso.status = "ARQUIVADO"
        curso_atualizado = await self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    async def upload_capa(self, curso_id: int, professor_id: int, arquivo: UploadFile) -> CursoResponse:
        curso = await self._obter_e_validar(curso_id, professor_id)

        extensao = arquivo.filename.split(".")[-1].lower()
        if extensao not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise ValueError("Formato de imagem não suportado")

        diretorio = f"uploads/capas_cursos/{curso_id}"
        os.makedirs(diretorio, exist_ok=True)

        from datetime import datetime
        timestamp = int(datetime.utcnow().timestamp())
        nome_arquivo = f"{timestamp}.{extensao}"
        caminho = os.path.join(diretorio, nome_arquivo)

        conteudo = await arquivo.read()
        with open(caminho, "wb") as f:
            f.write(conteudo)

        curso.capa = caminho
        curso_atualizado = await self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    async def _obter_e_validar(self, curso_id: int, professor_id: int) -> Curso:
        curso = await self.repository.find_by_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()
        return curso
