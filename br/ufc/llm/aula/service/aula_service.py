import os
import bleach
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.aula.dto.aula_dto import (
    AulaRequest, AulaEditarRequest, AulaResponse, ListaAulasResponse,
    ConteudoGeradoResponse, ConfirmarConteudoRequest,
)
from br.ufc.llm.aula.repository.aula_repository import AulaRepository
from br.ufc.llm.aula.exception.aula_exception import AulaNaoEncontradaException
from br.ufc.llm.modulo.repository.modulo_repository import ModuloRepository
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
from br.ufc.llm.curso.repository.curso_repository import CursoRepository
from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException

# Tags HTML permitidas pelo bleach
TAGS_PERMITIDAS = [
    "p", "b", "i", "u", "strong", "em", "br", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "a", "img",
    "table", "thead", "tbody", "tr", "th", "td", "span", "div"
]
ATRIBUTOS_PERMITIDOS = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "width", "height"],
    "*": ["class", "style"]
}


def sanitizar_html(conteudo: Optional[str]) -> Optional[str]:
    """Sanitizar HTML com bleach (RF24)"""
    if conteudo is None:
        return None
    return bleach.clean(conteudo, tags=TAGS_PERMITIDAS, attributes=ATRIBUTOS_PERMITIDOS, strip=True)


class AulaService:
    """Serviço de negócio para gerenciamento de aulas"""

    def __init__(self, session: Session):
        self.session = session
        self.repository = AulaRepository(session)
        self.modulo_repository = ModuloRepository(session)
        self.curso_repository = CursoRepository(session)

    def criar_aula(self, modulo_id: int, requisicao: AulaRequest, professor_id: int) -> AulaResponse:
        """Criar aula em um módulo (RF22, RF24)"""
        self._validar_acesso_modulo(modulo_id, professor_id)

        total = self.repository.count_by_modulo(modulo_id)
        ordem = total + 1

        aula = Aula(
            nome=requisicao.nome,
            ordem=ordem,
            conteudo_ck_editor=sanitizar_html(requisicao.conteudo_ck_editor),
            modulo_id=modulo_id
        )
        aula_criada = self.repository.create(aula)
        return AulaResponse.model_validate(aula_criada)

    def listar_aulas(self, modulo_id: int, professor_id: int) -> ListaAulasResponse:
        """Listar aulas de um módulo"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aulas = self.repository.find_by_modulo(modulo_id)
        return ListaAulasResponse(
            aulas=[AulaResponse.model_validate(a) for a in aulas],
            total=len(aulas)
        )

    def obter_aula(self, modulo_id: int, aula_id: int, professor_id: int) -> AulaResponse:
        """Obter aula por ID"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()
        return AulaResponse.model_validate(aula)

    def editar_aula(self, modulo_id: int, aula_id: int, requisicao: AulaEditarRequest, professor_id: int) -> AulaResponse:
        """Editar aula — sanitiza conteúdo HTML (RF24)"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()

        if requisicao.nome is not None:
            aula.nome = requisicao.nome
        if requisicao.conteudo_ck_editor is not None:
            aula.conteudo_ck_editor = sanitizar_html(requisicao.conteudo_ck_editor)

        aula_atualizada = self.repository.update(aula)
        return AulaResponse.model_validate(aula_atualizada)

    def deletar_aula(self, modulo_id: int, aula_id: int, professor_id: int) -> None:
        """Deletar aula"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()
        self.repository.delete(aula)

    def upload_arquivo(self, modulo_id: int, aula_id: int, professor_id: int, arquivo: UploadFile) -> AulaResponse:
        """Upload de arquivo (PDF ou vídeo) (RF23)"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()

        extensao = arquivo.filename.split(".")[-1].lower()
        if extensao == "pdf":
            tipo = "PDF"
        elif extensao in ["mp4", "avi", "mov", "mkv", "webm"]:
            tipo = "VIDEO"
        else:
            raise ValueError("Formato de arquivo não suportado. Use PDF ou vídeo (mp4, avi, mov, mkv, webm)")

        diretorio = f"uploads/arquivos_aulas/{aula_id}"
        os.makedirs(diretorio, exist_ok=True)

        from datetime import datetime
        timestamp = int(datetime.utcnow().timestamp())
        nome_arquivo = f"{timestamp}.{extensao}"
        caminho = os.path.join(diretorio, nome_arquivo)

        conteudo = arquivo.file.read()
        with open(caminho, "wb") as f:
            f.write(conteudo)

        aula.arquivo = caminho
        aula.tipo_arquivo = tipo
        aula_atualizada = self.repository.update(aula)
        return AulaResponse.model_validate(aula_atualizada)

    def gerar_conteudo(self, modulo_id: int, aula_id: int, professor_id: int) -> ConteudoGeradoResponse:
        """Gera conteúdo HTML via GPT-4o a partir do PDF e/ou CKEditor (RF26-RF27)"""
        from br.ufc.llm.shared.service.openai_service import gerar_conteudo_aula, extrair_texto_pdf

        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()

        partes = []
        if aula.arquivo and aula.tipo_arquivo == "PDF" and os.path.exists(aula.arquivo):
            partes.append(extrair_texto_pdf(aula.arquivo))
        if aula.conteudo_ck_editor:
            import re
            texto_ck = re.sub(r"<[^>]+>", " ", aula.conteudo_ck_editor).strip()
            if texto_ck:
                partes.append(texto_ck)

        if not partes:
            raise ValueError("A aula não possui conteúdo legível (PDF ou texto) para gerar conteúdo")

        html_gerado = gerar_conteudo_aula("\n\n".join(partes))
        return ConteudoGeradoResponse(conteudo_gerado=html_gerado)

    def confirmar_conteudo(
        self, modulo_id: int, aula_id: int, professor_id: int,
        requisicao: ConfirmarConteudoRequest
    ) -> AulaResponse:
        """Persiste o conteúdo gerado pela IA no campo conteudo_gerado (RF28)"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        aula = self.repository.find_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise AulaNaoEncontradaException()

        aula.conteudo_gerado = requisicao.conteudo_gerado
        aula_atualizada = self.repository.update(aula)
        return AulaResponse.model_validate(aula_atualizada)

    def _validar_acesso_modulo(self, modulo_id: int, professor_id: int):
        """Valida que professor tem acesso ao módulo"""
        modulo = self.modulo_repository.find_by_id(modulo_id)
        if not modulo:
            raise ModuloNaoEncontradoException()

        curso = self.curso_repository.find_by_id(modulo.curso_id)
        if not curso:
            raise ModuloNaoEncontradoException()
        if curso.professor_id != professor_id:
            raise CursoAcessoNegadoException()
