from typing import List
from sqlalchemy.orm import Session

from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa
from br.ufc.llm.prova.dto.prova_dto import (
    ProvaRequest, ProvaResponse,
    PerguntaRequest, PerguntaResponse,
    EstatisticasProvaResponse, PerguntaEstatisticaResponse, AlternativaEstatisticaResponse,
    QuizGeradoResponse, PerguntaQuizResponse, AlternativaQuizResponse,
)
from br.ufc.llm.prova.repository.prova_repository import ProvaRepository, PerguntaRepository
from br.ufc.llm.prova.exception.prova_exception import (
    ProvaNaoEncontradaException,
    ProvaJaExisteException,
    PerguntaNaoEncontradaException,
    PerguntaInvalidaException
)
from br.ufc.llm.modulo.repository.modulo_repository import ModuloRepository
from br.ufc.llm.modulo.exception.modulo_exception import ModuloNaoEncontradoException
from br.ufc.llm.curso.repository.curso_repository import CursoRepository
from br.ufc.llm.curso.exception.curso_exception import CursoAcessoNegadoException


class ProvaService:
    """Serviço de negócio para gerenciamento de provas"""

    def __init__(self, session: Session):
        self.session = session
        self.repository = ProvaRepository(session)
        self.pergunta_repository = PerguntaRepository(session)
        self.modulo_repository = ModuloRepository(session)
        self.curso_repository = CursoRepository(session)

    def criar_prova(self, modulo_id: int, requisicao: ProvaRequest, professor_id: int) -> ProvaResponse:
        """Criar prova vinculada a módulo (RF29)"""
        self._validar_acesso_modulo(modulo_id, professor_id)

        # Verificar se módulo já tem prova
        prova_existente = self.repository.find_by_modulo(modulo_id)
        if prova_existente:
            raise ProvaJaExisteException()

        prova = Prova(
            modulo_id=modulo_id,
            mostrar_respostas_erradas=requisicao.mostrar_respostas_erradas,
            mostrar_respostas_corretas=requisicao.mostrar_respostas_corretas,
            mostrar_valores=requisicao.mostrar_valores
        )
        prova_criada = self.repository.create(prova)
        return self._to_response(prova_criada)

    def obter_prova(self, modulo_id: int, professor_id: int) -> ProvaResponse:
        """Obter prova do módulo com perguntas"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        prova = self.repository.find_by_modulo(modulo_id)
        if not prova:
            raise ProvaNaoEncontradaException()
        return self._to_response(prova)

    def editar_prova(self, modulo_id: int, requisicao: ProvaRequest, professor_id: int) -> ProvaResponse:
        """Editar configurações da prova (RF32-RF33)"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        prova = self.repository.find_by_modulo(modulo_id)
        if not prova:
            raise ProvaNaoEncontradaException()

        prova.mostrar_respostas_erradas = requisicao.mostrar_respostas_erradas
        prova.mostrar_respostas_corretas = requisicao.mostrar_respostas_corretas
        prova.mostrar_valores = requisicao.mostrar_valores

        prova_atualizada = self.repository.update(prova)
        return self._to_response(prova_atualizada)

    def deletar_prova(self, modulo_id: int, professor_id: int) -> None:
        """Deletar prova"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        prova = self.repository.find_by_modulo(modulo_id)
        if not prova:
            raise ProvaNaoEncontradaException()
        self.repository.delete(prova)

    def adicionar_pergunta(self, prova_id: int, requisicao: PerguntaRequest, professor_id: int) -> PerguntaResponse:
        """Adicionar pergunta com alternativas (RF30, RF31)"""
        prova = self.repository.find_by_id(prova_id)
        if not prova:
            raise ProvaNaoEncontradaException()

        self._validar_acesso_modulo(prova.modulo_id, professor_id)
        self._validar_alternativas(requisicao.alternativas)

        total = self.pergunta_repository.count_by_prova(prova_id)
        ordem = total + 1

        pergunta = Pergunta(
            enunciado=requisicao.enunciado,
            pontos=requisicao.pontos,
            ordem=ordem,
            prova_id=prova_id
        )
        self.session.add(pergunta)
        self.session.flush()  # Para obter o ID

        for alt_req in requisicao.alternativas:
            alternativa = Alternativa(
                texto=alt_req.texto,
                correta=alt_req.correta,
                pergunta_id=pergunta.id
            )
            self.session.add(alternativa)

        self.session.commit()
        self.session.refresh(pergunta)
        return self._pergunta_to_response(pergunta)

    def editar_pergunta(self, prova_id: int, pergunta_id: int, requisicao: PerguntaRequest, professor_id: int) -> PerguntaResponse:
        """Editar pergunta e suas alternativas"""
        prova = self.repository.find_by_id(prova_id)
        if not prova:
            raise ProvaNaoEncontradaException()

        self._validar_acesso_modulo(prova.modulo_id, professor_id)

        pergunta = self.pergunta_repository.find_by_id(pergunta_id)
        if not pergunta or pergunta.prova_id != prova_id:
            raise PerguntaNaoEncontradaException()

        self._validar_alternativas(requisicao.alternativas)

        pergunta.enunciado = requisicao.enunciado
        pergunta.pontos = requisicao.pontos

        # Remover alternativas antigas e criar novas
        self.pergunta_repository.delete_alternativas(pergunta_id)

        for alt_req in requisicao.alternativas:
            alternativa = Alternativa(
                texto=alt_req.texto,
                correta=alt_req.correta,
                pergunta_id=pergunta_id
            )
            self.session.add(alternativa)

        self.session.commit()
        self.session.refresh(pergunta)
        return self._pergunta_to_response(pergunta)

    def deletar_pergunta(self, prova_id: int, pergunta_id: int, professor_id: int) -> None:
        """Deletar pergunta"""
        prova = self.repository.find_by_id(prova_id)
        if not prova:
            raise ProvaNaoEncontradaException()

        self._validar_acesso_modulo(prova.modulo_id, professor_id)

        pergunta = self.pergunta_repository.find_by_id(pergunta_id)
        if not pergunta or pergunta.prova_id != prova_id:
            raise PerguntaNaoEncontradaException()

        self.pergunta_repository.delete(pergunta)

    def gerar_quiz_ia(self, modulo_id: int, professor_id: int, num_perguntas: int = 5) -> QuizGeradoResponse:
        """Gera quiz via GPT-4o a partir do conteúdo do módulo (RF35-RF37)"""
        from br.ufc.llm.shared.service.openai_service import gerar_quiz, extrair_texto_pdf
        from br.ufc.llm.aula.repository.aula_repository import AulaRepository
        import re
        import os

        self._validar_acesso_modulo(modulo_id, professor_id)

        aula_repo = AulaRepository(self.session)
        aulas = aula_repo.find_by_modulo(modulo_id)

        partes = []
        for aula in aulas:
            if aula.arquivo and aula.tipo_arquivo == "PDF" and os.path.exists(aula.arquivo):
                partes.append(extrair_texto_pdf(aula.arquivo))
            for campo in (aula.conteudo_ck_editor, aula.conteudo_gerado):
                if campo:
                    texto = re.sub(r"<[^>]+>", " ", campo).strip()
                    if texto:
                        partes.append(texto)

        if not partes:
            raise ValueError("O módulo não possui conteúdo legível para gerar o quiz")

        perguntas_raw = gerar_quiz("\n\n".join(partes), num_perguntas)

        perguntas = [
            PerguntaQuizResponse(
                enunciado=p["enunciado"],
                pontos=p.get("pontos", 1),
                alternativas=[
                    AlternativaQuizResponse(texto=a["texto"], correta=a["correta"])
                    for a in p["alternativas"]
                ]
            )
            for p in perguntas_raw
        ]
        return QuizGeradoResponse(perguntas=perguntas)

    def obter_estatisticas(self, modulo_id: int, professor_id: int) -> EstatisticasProvaResponse:
        """Estatísticas de respostas da prova (RF34)"""
        self._validar_acesso_modulo(modulo_id, professor_id)
        prova = self.repository.find_by_modulo(modulo_id)
        if not prova:
            raise ProvaNaoEncontradaException()

        perguntas = self.pergunta_repository.find_by_prova(prova.id)
        contagem = self.pergunta_repository.count_respostas_por_alternativa(prova.id)
        total_respondentes = self.pergunta_repository.count_respondentes(prova.id)

        perguntas_stat = []
        for pergunta in perguntas:
            total_pergunta = sum(contagem.get(a.id, 0) for a in pergunta.alternativas)
            alternativas_stat = []
            for alt in pergunta.alternativas:
                total_alt = contagem.get(alt.id, 0)
                percentual = round((total_alt / total_pergunta * 100), 1) if total_pergunta > 0 else 0.0
                alternativas_stat.append(AlternativaEstatisticaResponse(
                    alternativa_id=alt.id,
                    texto=alt.texto,
                    total_respostas=total_alt,
                    percentual=percentual
                ))
            perguntas_stat.append(PerguntaEstatisticaResponse(
                pergunta_id=pergunta.id,
                enunciado=pergunta.enunciado,
                total_respostas=total_pergunta,
                alternativas=alternativas_stat
            ))

        return EstatisticasProvaResponse(
            prova_id=prova.id,
            total_respondentes=total_respondentes,
            perguntas=perguntas_stat
        )

    def _validar_alternativas(self, alternativas: list) -> None:
        """Valida que há mínimo 2 alternativas e exatamente 1 correta (RF30)"""
        if len(alternativas) < 2:
            raise PerguntaInvalidaException("A pergunta deve ter no mínimo 2 alternativas")

        corretas = sum(1 for a in alternativas if a.correta)
        if corretas == 0:
            raise PerguntaInvalidaException("A pergunta deve ter exatamente 1 alternativa correta")
        if corretas > 1:
            raise PerguntaInvalidaException("A pergunta deve ter exatamente 1 alternativa correta")

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

    def _to_response(self, prova: Prova) -> ProvaResponse:
        """Converter prova para DTO de resposta"""
        perguntas = self.pergunta_repository.find_by_prova(prova.id)
        return ProvaResponse(
            id=prova.id,
            modulo_id=prova.modulo_id,
            mostrar_respostas_erradas=prova.mostrar_respostas_erradas,
            mostrar_respostas_corretas=prova.mostrar_respostas_corretas,
            mostrar_valores=prova.mostrar_valores,
            perguntas=[self._pergunta_to_response(p) for p in perguntas]
        )

    def _pergunta_to_response(self, pergunta: Pergunta) -> PerguntaResponse:
        """Converter pergunta para DTO de resposta"""
        from br.ufc.llm.prova.dto.prova_dto import AlternativaResponse
        return PerguntaResponse(
            id=pergunta.id,
            enunciado=pergunta.enunciado,
            pontos=pergunta.pontos,
            ordem=pergunta.ordem,
            prova_id=pergunta.prova_id,
            alternativas=[
                AlternativaResponse(
                    id=a.id,
                    texto=a.texto,
                    correta=a.correta,
                    pergunta_id=a.pergunta_id
                ) for a in pergunta.alternativas
            ]
        )
