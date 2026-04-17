from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from br.ufc.llm.matricula.repository.matricula_repository import MatriculaRepository
from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva
from br.ufc.llm.matricula.dto.matricula_dto import (
    MatriculaRequest,
    MatriculaResponse,
    ListaMatriculasResponse,
    CursoResumidoResponse,
    ListaCatalogoCursosResponse,
    ModuloResumidoResponse,
    ListaModulosResponse,
    AulaResumidaResponse,
    AulaCompletaResponse,
    ListaAulasResponse,
    ProvaSemGabaritoResponse,
    PerguntaSemGabaritoResponse,
    AlternativaSemGabaritoResponse,
    RespostaItemRequest,
    ResultadoProvaResponse,
    RespostaProvaResponse,
)
from br.ufc.llm.matricula.exception.matricula_exception import (
    MatriculaJaExisteException,
    MatriculaNaoEncontradaException,
    CursoNaoPublicadoException,
    AcessoNegadoMatriculaException,
    PerfilInvalidoException,
    DadosMatriculaObrigatoriosException,
    RespostaJaExisteException,
    RespostasIncompletasException,
    ResultadoNaoEncontradoException,
)


class MatriculaService:

    def __init__(self, session: AsyncSession):
        self.repo = MatriculaRepository(session)

    async def listar_catalogo(self, q: Optional[str] = None) -> ListaCatalogoCursosResponse:
        cursos = await self.repo.find_cursos_publicados(q)
        return ListaCatalogoCursosResponse(
            cursos=[CursoResumidoResponse.model_validate(c) for c in cursos],
            total=len(cursos)
        )

    async def obter_curso_publicado(self, curso_id: int) -> CursoResumidoResponse:
        curso = await self.repo.find_curso_publicado_by_id(curso_id)
        if not curso:
            raise CursoNaoPublicadoException()
        return CursoResumidoResponse.model_validate(curso)

    async def matricular(self, aluno_id: int, perfil: str, requisicao: MatriculaRequest) -> MatriculaResponse:
        if perfil != "ALUNO":
            raise PerfilInvalidoException()

        curso = await self.repo.find_curso_publicado_by_id(requisicao.curso_id)
        if not curso:
            raise CursoNaoPublicadoException()

        existente = await self.repo.find_by_aluno_and_curso(aluno_id, requisicao.curso_id)
        if existente:
            raise MatriculaJaExisteException()

        if curso.requer_endereco and not requisicao.endereco:
            raise DadosMatriculaObrigatoriosException("endereco")
        if curso.requer_genero and not requisicao.genero:
            raise DadosMatriculaObrigatoriosException("genero")
        if curso.requer_idade and requisicao.idade is None:
            raise DadosMatriculaObrigatoriosException("idade")

        matricula = Matricula(
            aluno_id=aluno_id,
            curso_id=requisicao.curso_id,
            endereco=requisicao.endereco,
            genero=requisicao.genero,
            idade=requisicao.idade
        )
        matricula = await self.repo.create(matricula)
        return MatriculaResponse.model_validate(matricula)

    async def listar_minhas_matriculas(self, aluno_id: int) -> ListaMatriculasResponse:
        matriculas = await self.repo.find_by_aluno(aluno_id)
        return ListaMatriculasResponse(
            matriculas=[MatriculaResponse.model_validate(m) for m in matriculas],
            total=len(matriculas)
        )

    async def _verificar_matricula(self, aluno_id: int, curso_id: int) -> None:
        matricula = await self.repo.find_by_aluno_and_curso(aluno_id, curso_id)
        if not matricula:
            raise AcessoNegadoMatriculaException()

    async def listar_modulos(self, aluno_id: int, curso_id: int) -> ListaModulosResponse:
        await self._verificar_matricula(aluno_id, curso_id)
        modulos = await self.repo.find_modulos_by_curso(curso_id)
        return ListaModulosResponse(
            modulos=[ModuloResumidoResponse.model_validate(m) for m in modulos],
            total=len(modulos)
        )

    async def listar_aulas(self, aluno_id: int, curso_id: int, modulo_id: int) -> ListaAulasResponse:
        await self._verificar_matricula(aluno_id, curso_id)
        aulas = await self.repo.find_aulas_by_modulo(modulo_id)
        return ListaAulasResponse(
            aulas=[AulaResumidaResponse.model_validate(a) for a in aulas],
            total=len(aulas)
        )

    async def obter_aula(self, aluno_id: int, curso_id: int, modulo_id: int, aula_id: int) -> AulaCompletaResponse:
        await self._verificar_matricula(aluno_id, curso_id)
        aula = await self.repo.find_aula_by_id(aula_id)
        if not aula or aula.modulo_id != modulo_id:
            raise MatriculaNaoEncontradaException()
        return AulaCompletaResponse.model_validate(aula)

    async def obter_prova(self, aluno_id: int, curso_id: int, modulo_id: int) -> ProvaSemGabaritoResponse:
        await self._verificar_matricula(aluno_id, curso_id)
        prova = await self.repo.find_prova_by_modulo(modulo_id)
        if not prova:
            raise MatriculaNaoEncontradaException()

        perguntas = [
            PerguntaSemGabaritoResponse(
                id=p.id,
                enunciado=p.enunciado,
                ordem=p.ordem,
                alternativas=[
                    AlternativaSemGabaritoResponse(id=a.id, texto=a.texto)
                    for a in p.alternativas
                ]
            )
            for p in prova.perguntas
        ]
        return ProvaSemGabaritoResponse(
            id=prova.id,
            modulo_id=prova.modulo_id,
            perguntas=perguntas
        )

    async def responder_prova(
        self,
        aluno_id: int,
        prova_id: int,
        respostas: List[RespostaItemRequest]
    ) -> None:
        prova = await self.repo.find_prova_by_id(prova_id)
        if not prova:
            raise MatriculaNaoEncontradaException()

        curso_id = prova.modulo.curso_id
        await self._verificar_matricula(aluno_id, curso_id)

        if not respostas:
            raise RespostasIncompletasException()

        total_perguntas = len(prova.perguntas)
        if len(respostas) < total_perguntas:
            raise RespostasIncompletasException()

        for item in respostas:
            existente = await self.repo.find_resposta_by_aluno_and_pergunta(aluno_id, item.pergunta_id)
            if existente:
                raise RespostaJaExisteException()

            resposta = RespostaProva(
                aluno_id=aluno_id,
                prova_id=prova_id,
                pergunta_id=item.pergunta_id,
                alternativa_id=item.alternativa_id
            )
            await self.repo.create_resposta(resposta)

    async def obter_resultado(self, aluno_id: int, prova_id: int) -> ResultadoProvaResponse:
        prova = await self.repo.find_prova_by_id(prova_id)
        if not prova:
            raise MatriculaNaoEncontradaException()

        curso_id = prova.modulo.curso_id
        await self._verificar_matricula(aluno_id, curso_id)

        respostas = await self.repo.find_respostas_by_aluno_and_prova(aluno_id, prova_id)
        if not respostas:
            raise ResultadoNaoEncontradoException()

        perguntas_map = {p.id: p for p in prova.perguntas}
        alternativas_map = {
            a.id: a
            for p in prova.perguntas
            for a in p.alternativas
        }

        pontuacao_obtida = 0.0
        pontuacao_maxima = sum(p.pontos for p in prova.perguntas)

        detalhes = []
        for resposta in respostas:
            pergunta = perguntas_map.get(resposta.pergunta_id)
            alternativa_escolhida = alternativas_map.get(resposta.alternativa_id)
            if not pergunta or not alternativa_escolhida:
                continue

            acertou = alternativa_escolhida.correta
            if acertou:
                pontuacao_obtida += pergunta.pontos

            alternativa_correta = next(
                (a.id for a in pergunta.alternativas if a.correta), None
            )

            detalhes.append(RespostaProvaResponse(
                pergunta_id=pergunta.id,
                enunciado=pergunta.enunciado,
                alternativa_escolhida_id=resposta.alternativa_id,
                acertou=acertou if prova.mostrar_respostas_erradas or prova.mostrar_respostas_corretas else None,
                alternativa_correta_id=alternativa_correta if prova.mostrar_respostas_corretas else None,
                pontos_obtidos=float(pergunta.pontos) if acertou else 0.0,
                pontos_possiveis=float(pergunta.pontos)
            ))

        perguntas_resultado = detalhes if (prova.mostrar_respostas_erradas or prova.mostrar_respostas_corretas) else None

        return ResultadoProvaResponse(
            prova_id=prova_id,
            pontuacao_obtida=pontuacao_obtida,
            pontuacao_maxima=pontuacao_maxima,
            perguntas=perguntas_resultado
        )
