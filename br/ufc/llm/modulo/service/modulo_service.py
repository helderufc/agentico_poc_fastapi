import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from br.ufc.llm.modulo.domain.modulo import Modulo
from br.ufc.llm.modulo.dto.modulo_dto import ModuloEditarRequest, ModuloResponse, ListaModulosResponse
from br.ufc.llm.modulo.repository.modulo_repository import ModuloRepository
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException, ModuloAcessoNegadoException
from br.ufc.llm.curso.repository.curso_repository import CursoRepository
from br.ufc.llm.curso.exception.curso_exception import CursoNaoEncontradoException, CursoAcessoNegadoException


class ModuloService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ModuloRepository(session)
        self.curso_repository = CursoRepository(session)

    async def criar_modulo(self, curso_id: int, professor_id: int) -> ModuloResponse:
        curso = await self.curso_repository.find_by_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()

        total = await self.repository.count_by_curso(curso_id)
        ordem = total + 1
        nome = f"Módulo {ordem:02d}"

        modulo = Modulo(nome=nome, ordem=ordem, curso_id=curso_id)
        modulo_criado = await self.repository.create(modulo)
        return ModuloResponse.model_validate(modulo_criado)

    async def listar_modulos(self, curso_id: int, professor_id: int) -> ListaModulosResponse:
        curso = await self.curso_repository.find_by_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()

        modulos = await self.repository.find_by_curso(curso_id)
        return ListaModulosResponse(
            modulos=[ModuloResponse.model_validate(m) for m in modulos],
            total=len(modulos)
        )

    async def obter_modulo(self, curso_id: int, modulo_id: int, professor_id: int) -> ModuloResponse:
        await self._validar_acesso_curso(curso_id, professor_id)
        modulo = await self.repository.find_by_id(modulo_id)
        if not modulo or modulo.curso_id != curso_id:
            raise ModuloNaoEncontradoException()
        return ModuloResponse.model_validate(modulo)

    async def editar_modulo(self, curso_id: int, modulo_id: int, requisicao: ModuloEditarRequest, professor_id: int) -> ModuloResponse:
        await self._validar_acesso_curso(curso_id, professor_id)
        modulo = await self.repository.find_by_id(modulo_id)
        if not modulo or modulo.curso_id != curso_id:
            raise ModuloNaoEncontradoException()

        if requisicao.nome is not None:
            modulo.nome = requisicao.nome

        modulo_atualizado = await self.repository.update(modulo)
        return ModuloResponse.model_validate(modulo_atualizado)

    async def deletar_modulo(self, curso_id: int, modulo_id: int, professor_id: int) -> None:
        await self._validar_acesso_curso(curso_id, professor_id)
        modulo = await self.repository.find_by_id(modulo_id)
        if not modulo or modulo.curso_id != curso_id:
            raise ModuloNaoEncontradoException()

        ordem_deletado = modulo.ordem
        await self.repository.delete(modulo)

        modulos_restantes = await self.repository.find_by_curso(curso_id)
        for m in modulos_restantes:
            if m.ordem > ordem_deletado:
                nova_ordem = m.ordem - 1
                m.ordem = nova_ordem
                m.nome = f"Módulo {nova_ordem:02d}"
                await self.repository.update(m)

    async def upload_capa(self, curso_id: int, modulo_id: int, professor_id: int, arquivo: UploadFile) -> ModuloResponse:
        await self._validar_acesso_curso(curso_id, professor_id)
        modulo = await self.repository.find_by_id(modulo_id)
        if not modulo or modulo.curso_id != curso_id:
            raise ModuloNaoEncontradoException()

        extensao = arquivo.filename.split(".")[-1].lower()
        if extensao not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise ValueError("Formato de imagem não suportado")

        diretorio = f"uploads/capas_modulos/{modulo_id}"
        os.makedirs(diretorio, exist_ok=True)

        from datetime import datetime
        timestamp = int(datetime.utcnow().timestamp())
        nome_arquivo = f"{timestamp}.{extensao}"
        caminho = os.path.join(diretorio, nome_arquivo)

        conteudo = await arquivo.read()
        with open(caminho, "wb") as f:
            f.write(conteudo)

        modulo.capa = caminho
        modulo_atualizado = await self.repository.update(modulo)
        return ModuloResponse.model_validate(modulo_atualizado)

    async def _validar_acesso_curso(self, curso_id: int, professor_id: int):
        curso = await self.curso_repository.find_by_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()
