import os
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.curso.dto.curso_dto import CursoRequest, CursoResponse, ListaCursosResponse
from br.ufc.llm.curso.repository.curso_repository import CursoRepository
from br.ufc.llm.curso.exception.curso_exception import (
    CursoNaoEncontradoException,
    CursoAcessoNegadoException
)


class CursoService:
    """Serviço de negócio para gerenciamento de cursos"""

    def __init__(self, session: Session):
        self.session = session
        self.repository = CursoRepository(session)

    def criar_curso(self, requisicao: CursoRequest, professor_id: int) -> CursoResponse:
        """Criar novo curso (RF09, RF11, RF14)"""
        curso = Curso(
            titulo=requisicao.titulo,
            categoria=requisicao.categoria.upper(),  # RF11: uppercase
            descricao=requisicao.descricao,
            carga_horaria=requisicao.carga_horaria,
            requer_endereco=requisicao.requer_endereco,
            requer_genero=requisicao.requer_genero,
            requer_idade=requisicao.requer_idade,
            status="RASCUNHO",  # RF14: padrão RASCUNHO
            professor_id=professor_id
        )
        curso_criado = self.repository.create(curso)
        return CursoResponse.model_validate(curso_criado)

    def listar_cursos(
        self,
        professor_id: int,
        status: Optional[str] = None,
        q: Optional[str] = None
    ) -> ListaCursosResponse:
        """Listar cursos do professor (RF15, RF17)"""
        cursos, total = self.repository.find_by_professor(professor_id, status, q)
        return ListaCursosResponse(
            cursos=[CursoResponse.model_validate(c) for c in cursos],
            total=total
        )

    def obter_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        """Obter curso por ID (RF09) — valida ownership"""
        curso = self._obter_e_validar(curso_id, professor_id)
        return CursoResponse.model_validate(curso)

    def editar_curso(self, curso_id: int, requisicao: CursoRequest, professor_id: int) -> CursoResponse:
        """Editar curso (RF16)"""
        curso = self._obter_e_validar(curso_id, professor_id)

        curso.titulo = requisicao.titulo
        curso.categoria = requisicao.categoria.upper()
        curso.descricao = requisicao.descricao
        curso.carga_horaria = requisicao.carga_horaria
        curso.requer_endereco = requisicao.requer_endereco
        curso.requer_genero = requisicao.requer_genero
        curso.requer_idade = requisicao.requer_idade

        curso_atualizado = self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    def deletar_curso(self, curso_id: int, professor_id: int) -> None:
        """Deletar curso (RF09)"""
        curso = self._obter_e_validar(curso_id, professor_id)
        self.repository.delete(curso)

    def publicar_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        """Publicar curso (RF14)"""
        curso = self._obter_e_validar(curso_id, professor_id)
        curso.status = "PUBLICADO"
        curso_atualizado = self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    def arquivar_curso(self, curso_id: int, professor_id: int) -> CursoResponse:
        """Arquivar curso (RF14)"""
        curso = self._obter_e_validar(curso_id, professor_id)
        curso.status = "ARQUIVADO"
        curso_atualizado = self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    def upload_capa(self, curso_id: int, professor_id: int, arquivo: UploadFile) -> CursoResponse:
        """Upload de capa do curso (RF10)"""
        curso = self._obter_e_validar(curso_id, professor_id)

        extensao = arquivo.filename.split(".")[-1].lower()
        if extensao not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise ValueError("Formato de imagem não suportado")

        diretorio = f"uploads/capas_cursos/{curso_id}"
        os.makedirs(diretorio, exist_ok=True)

        from datetime import datetime
        timestamp = int(datetime.utcnow().timestamp())
        nome_arquivo = f"{timestamp}.{extensao}"
        caminho = os.path.join(diretorio, nome_arquivo)

        conteudo = arquivo.file.read()
        with open(caminho, "wb") as f:
            f.write(conteudo)

        curso.capa = caminho
        curso_atualizado = self.repository.update(curso)
        return CursoResponse.model_validate(curso_atualizado)

    def _obter_e_validar(self, curso_id: int, professor_id: int) -> Curso:
        """Obter curso e validar que o professor é o dono"""
        curso = self.repository.find_by_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()
        return curso
