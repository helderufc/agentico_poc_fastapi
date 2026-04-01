"""
Testes da Fase 2 — Perfil ALUNO
US-AL02: Buscar cursos publicados
US-AL03: Matricular-se em curso
US-AL04: Acessar aulas de um módulo
US-AL05: Acessar arquivo da aula
US-AL06: Fazer prova e submeter respostas
US-AL07: Ver resultado da prova
"""
import pytest
from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.modulo.domain.modulo import Modulo
from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.prova.domain.prova import Prova, Pergunta, Alternativa
from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva


# ===========================================================================
# Fixtures específicas de matrícula
# ===========================================================================

@pytest.fixture
def curso_com_requisitos(db_session, usuario_professor, client):
    """Curso publicado que requer endereço e gênero"""
    curso = Curso(
        titulo="Curso com Requisitos",
        categoria="TI",
        descricao="Curso que requer dados extras",
        carga_horaria="20h",
        professor_id=usuario_professor.id,
        status="PUBLICADO",
        requer_endereco=True,
        requer_genero=True,
        requer_idade=False
    )
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


@pytest.fixture
def curso_publicado_simples(db_session, usuario_professor, client):
    """Curso publicado sem requisitos extras"""
    curso = Curso(
        titulo="Curso Publicado Simples",
        categoria="TI",
        descricao="Curso sem requisitos",
        carga_horaria="10h",
        professor_id=usuario_professor.id,
        status="PUBLICADO"
    )
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


@pytest.fixture
def modulo_do_curso_publicado(db_session, curso_publicado_simples, client):
    """Módulo dentro do curso publicado simples"""
    modulo = Modulo(
        nome="Módulo 01",
        ordem=1,
        curso_id=curso_publicado_simples.id
    )
    db_session.add(modulo)
    db_session.commit()
    db_session.refresh(modulo)
    return modulo


@pytest.fixture
def aula_do_modulo(db_session, modulo_do_curso_publicado, client):
    """Aula dentro do módulo do curso publicado"""
    aula = Aula(
        nome="Aula 01",
        ordem=1,
        conteudo_ck_editor="<p>Conteúdo da aula 01</p>",
        modulo_id=modulo_do_curso_publicado.id
    )
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


@pytest.fixture
def prova_do_modulo(db_session, modulo_do_curso_publicado, client):
    """Prova com perguntas e alternativas no módulo do curso publicado"""
    prova = Prova(
        modulo_id=modulo_do_curso_publicado.id,
        mostrar_respostas_erradas=True,
        mostrar_respostas_corretas=True,
        mostrar_valores=True
    )
    db_session.add(prova)
    db_session.commit()
    db_session.refresh(prova)

    pergunta = Pergunta(
        enunciado="Qual é a capital do Brasil?",
        pontos=2,
        ordem=1,
        prova_id=prova.id
    )
    db_session.add(pergunta)
    db_session.commit()
    db_session.refresh(pergunta)

    alt_correta = Alternativa(texto="Brasília", correta=True, pergunta_id=pergunta.id)
    alt_errada = Alternativa(texto="São Paulo", correta=False, pergunta_id=pergunta.id)
    db_session.add_all([alt_correta, alt_errada])
    db_session.commit()
    db_session.refresh(alt_correta)
    db_session.refresh(alt_errada)

    return prova


@pytest.fixture
def matricula_aluno(db_session, usuario_aluno, curso_publicado_simples, client):
    """Matrícula do aluno no curso publicado simples"""
    matricula = Matricula(
        aluno_id=usuario_aluno.id,
        curso_id=curso_publicado_simples.id
    )
    db_session.add(matricula)
    db_session.commit()
    db_session.refresh(matricula)
    return matricula


# ===========================================================================
# US-AL02: Catálogo de cursos publicados
# ===========================================================================

class TestCatalogoCursos:
    """Testes para listagem de cursos publicados (US-AL02)"""

    def test_listar_cursos_publicados(self, client, headers_aluno, curso_publicado_simples):
        """Aluno lista cursos publicados"""
        response = client.get("/api/v1/catalogo/cursos", headers=headers_aluno)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["cursos"]) >= 1
        assert all(c["status"] == "PUBLICADO" for c in data["cursos"])

    def test_catalogo_nao_retorna_rascunhos(self, client, headers_aluno, db_session, usuario_professor):
        """Catálogo não exibe cursos em rascunho"""
        curso_rascunho = Curso(
            titulo="Rascunho Oculto",
            categoria="TI",
            descricao="Não deve aparecer",
            carga_horaria="5h",
            professor_id=usuario_professor.id,
            status="RASCUNHO"
        )
        db_session.add(curso_rascunho)
        db_session.commit()

        response = client.get("/api/v1/catalogo/cursos", headers=headers_aluno)
        assert response.status_code == 200
        titulos = [c["titulo"] for c in response.json()["data"]["cursos"]]
        assert "Rascunho Oculto" not in titulos

    def test_catalogo_busca_por_titulo(self, client, headers_aluno, curso_publicado_simples):
        """Busca por texto no título"""
        response = client.get(
            f"/api/v1/catalogo/cursos?q=Simples",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert any("Simples" in c["titulo"] for c in data["cursos"])

    def test_catalogo_busca_sem_resultado(self, client, headers_aluno):
        """Busca sem resultado retorna lista vazia"""
        response = client.get(
            "/api/v1/catalogo/cursos?q=xyzXYZnaoencontrado",
            headers=headers_aluno
        )
        assert response.status_code == 200
        assert response.json()["data"]["cursos"] == []

    def test_catalogo_detalhe_curso_publicado(self, client, headers_aluno, curso_publicado_simples):
        """Aluno obtém detalhe de curso publicado"""
        response = client.get(
            f"/api/v1/catalogo/cursos/{curso_publicado_simples.id}",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == curso_publicado_simples.id
        assert data["status"] == "PUBLICADO"

    def test_catalogo_detalhe_curso_nao_publicado_retorna_404(self, client, headers_aluno, db_session, usuario_professor):
        """Detalhe de curso não publicado retorna 404"""
        curso = Curso(
            titulo="Arquivado",
            categoria="TI",
            descricao="Desc",
            carga_horaria="1h",
            professor_id=usuario_professor.id,
            status="ARQUIVADO"
        )
        db_session.add(curso)
        db_session.commit()

        response = client.get(f"/api/v1/catalogo/cursos/{curso.id}", headers=headers_aluno)
        assert response.status_code == 404

    def test_catalogo_professor_tambem_acessa(self, client, headers_professor, curso_publicado_simples):
        """Professor também pode ver o catálogo"""
        response = client.get("/api/v1/catalogo/cursos", headers=headers_professor)
        assert response.status_code == 200

    def test_catalogo_sem_autenticacao_retorna_401(self, client, curso_publicado_simples):
        """Acesso sem token retorna 401"""
        response = client.get("/api/v1/catalogo/cursos")
        assert response.status_code == 401


# ===========================================================================
# US-AL03: Matrícula em curso
# ===========================================================================

class TestMatricula:
    """Testes para matrícula em curso (US-AL03)"""

    def test_matricular_com_sucesso(self, client, headers_aluno, curso_publicado_simples):
        """Aluno se matricula em curso publicado"""
        body = {"curso_id": curso_publicado_simples.id}
        response = client.post("/api/v1/matriculas", json=body, headers=headers_aluno)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["curso_id"] == curso_publicado_simples.id

    def test_matricular_curso_nao_publicado_retorna_400(self, client, headers_aluno, db_session, usuario_professor):
        """Aluno não pode se matricular em curso não publicado"""
        curso = Curso(
            titulo="Rascunho",
            categoria="TI",
            descricao="Desc",
            carga_horaria="1h",
            professor_id=usuario_professor.id,
            status="RASCUNHO"
        )
        db_session.add(curso)
        db_session.commit()

        body = {"curso_id": curso.id}
        response = client.post("/api/v1/matriculas", json=body, headers=headers_aluno)
        assert response.status_code == 400

    def test_matricular_duas_vezes_retorna_409(self, client, headers_aluno, curso_publicado_simples, matricula_aluno):
        """Aluno não pode se matricular duas vezes"""
        body = {"curso_id": curso_publicado_simples.id}
        response = client.post("/api/v1/matriculas", json=body, headers=headers_aluno)
        assert response.status_code == 409

    def test_professor_nao_pode_se_matricular(self, client, headers_professor, curso_publicado_simples):
        """Professor não pode se matricular (perfil inválido)"""
        body = {"curso_id": curso_publicado_simples.id}
        response = client.post("/api/v1/matriculas", json=body, headers=headers_professor)
        assert response.status_code == 403

    def test_matricular_curso_com_requisitos_sem_dados_retorna_400(
        self, client, headers_aluno, curso_com_requisitos
    ):
        """Matrícula sem dados obrigatórios retorna 400"""
        body = {"curso_id": curso_com_requisitos.id}
        response = client.post("/api/v1/matriculas", json=body, headers=headers_aluno)
        assert response.status_code == 400

    def test_matricular_curso_com_requisitos_com_dados(
        self, client, headers_aluno, curso_com_requisitos
    ):
        """Matrícula com dados obrigatórios preenchidos"""
        body = {
            "curso_id": curso_com_requisitos.id,
            "endereco": "Rua das Flores, 123",
            "genero": "MASCULINO"
        }
        response = client.post("/api/v1/matriculas", json=body, headers=headers_aluno)
        assert response.status_code == 201

    def test_listar_minhas_matriculas(self, client, headers_aluno, matricula_aluno):
        """Aluno lista suas matrículas"""
        response = client.get("/api/v1/matriculas", headers=headers_aluno)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["matriculas"]) >= 1

    def test_matricular_sem_autenticacao_retorna_401(self, client, curso_publicado_simples):
        """Matrícula sem token retorna 401"""
        body = {"curso_id": curso_publicado_simples.id}
        response = client.post("/api/v1/matriculas", json=body)
        assert response.status_code == 401


# ===========================================================================
# US-AL04: Acesso ao conteúdo do curso
# ===========================================================================

class TestConteudoCurso:
    """Testes para acesso ao conteúdo (US-AL04, US-AL05)"""

    def test_listar_modulos_matriculado(
        self, client, headers_aluno, matricula_aluno,
        modulo_do_curso_publicado, curso_publicado_simples
    ):
        """Aluno matriculado lista módulos do curso"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["modulos"]) >= 1

    def test_listar_modulos_sem_matricula_retorna_403(
        self, client, headers_aluno, curso_publicado_simples, modulo_do_curso_publicado
    ):
        """Aluno não matriculado não acessa módulos"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos",
            headers=headers_aluno
        )
        assert response.status_code == 403

    def test_listar_aulas_matriculado(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, aula_do_modulo
    ):
        """Aluno matriculado lista aulas do módulo"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/aulas",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["aulas"]) >= 1

    def test_listar_aulas_sem_matricula_retorna_403(
        self, client, headers_aluno, curso_publicado_simples,
        modulo_do_curso_publicado, aula_do_modulo
    ):
        """Aluno não matriculado não acessa aulas"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/aulas",
            headers=headers_aluno
        )
        assert response.status_code == 403

    def test_obter_aula_completa(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, aula_do_modulo
    ):
        """Aluno matriculado obtém aula completa com conteúdo"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/aulas/{aula_do_modulo.id}",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == aula_do_modulo.id
        assert data["conteudo_ck_editor"] is not None

    def test_obter_aula_sem_matricula_retorna_403(
        self, client, headers_aluno, curso_publicado_simples,
        modulo_do_curso_publicado, aula_do_modulo
    ):
        """Aluno não matriculado não obtém aula"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/aulas/{aula_do_modulo.id}",
            headers=headers_aluno
        )
        assert response.status_code == 403


# ===========================================================================
# US-AL06 e US-AL07: Prova e Resultado
# ===========================================================================

class TestProvaAluno:
    """Testes para prova e resultado (US-AL06, US-AL07)"""

    def test_obter_prova_sem_gabarito(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo
    ):
        """Prova retornada sem indicar qual alternativa é correta"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/prova",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "perguntas" in data
        # Verificar que campo 'correta' não está nas alternativas
        for pergunta in data["perguntas"]:
            for alt in pergunta["alternativas"]:
                assert "correta" not in alt

    def test_obter_prova_sem_matricula_retorna_403(
        self, client, headers_aluno, curso_publicado_simples,
        modulo_do_curso_publicado, prova_do_modulo
    ):
        """Aluno não matriculado não acessa prova"""
        response = client.get(
            f"/api/v1/matriculas/{curso_publicado_simples.id}/modulos/{modulo_do_curso_publicado.id}/prova",
            headers=headers_aluno
        )
        assert response.status_code == 403

    def test_responder_prova_com_sucesso(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session
    ):
        """Aluno responde prova com sucesso"""
        # Recarregar para ter perguntas e alternativas
        db_session.refresh(prova_do_modulo)
        pergunta = prova_do_modulo.perguntas[0]
        alternativa = pergunta.alternativas[0]

        body = [{"pergunta_id": pergunta.id, "alternativa_id": alternativa.id}]
        response = client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )
        assert response.status_code == 201

    def test_responder_prova_sem_matricula_retorna_403(
        self, client, headers_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session
    ):
        """Aluno não matriculado não pode responder prova"""
        db_session.refresh(prova_do_modulo)
        pergunta = prova_do_modulo.perguntas[0]
        alternativa = pergunta.alternativas[0]

        body = [{"pergunta_id": pergunta.id, "alternativa_id": alternativa.id}]
        response = client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )
        assert response.status_code == 403

    def test_responder_prova_duas_vezes_retorna_409(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session
    ):
        """Aluno não pode responder mesma pergunta duas vezes"""
        db_session.refresh(prova_do_modulo)
        pergunta = prova_do_modulo.perguntas[0]
        alternativa = pergunta.alternativas[0]

        body = [{"pergunta_id": pergunta.id, "alternativa_id": alternativa.id}]
        # Primeira submissão
        client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )
        # Segunda submissão
        response = client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )
        assert response.status_code == 409

    def test_ver_resultado_prova(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session, usuario_aluno
    ):
        """Aluno vê resultado da prova"""
        db_session.refresh(prova_do_modulo)
        pergunta = prova_do_modulo.perguntas[0]
        alternativa_correta = next(a for a in pergunta.alternativas if a.correta)

        # Submeter resposta correta
        body = [{"pergunta_id": pergunta.id, "alternativa_id": alternativa_correta.id}]
        client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )

        response = client.get(
            f"/api/v1/provas/{prova_do_modulo.id}/resultado",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "pontuacao_obtida" in data
        assert "pontuacao_maxima" in data
        assert data["pontuacao_obtida"] == pergunta.pontos
        assert data["pontuacao_maxima"] == pergunta.pontos

    def test_resultado_mostra_respostas_erradas_quando_configurado(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session
    ):
        """Resultado inclui info de respostas erradas quando configurado"""
        db_session.refresh(prova_do_modulo)
        pergunta = prova_do_modulo.perguntas[0]
        alternativa_errada = next(a for a in pergunta.alternativas if not a.correta)

        # Submeter resposta errada
        body = [{"pergunta_id": pergunta.id, "alternativa_id": alternativa_errada.id}]
        client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )

        response = client.get(
            f"/api/v1/provas/{prova_do_modulo.id}/resultado",
            headers=headers_aluno
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # prova_do_modulo tem mostrar_respostas_erradas=True
        assert "perguntas" in data
        # Deve indicar que a resposta foi errada
        assert data["perguntas"][0]["acertou"] is False

    def test_resultado_sem_resposta_retorna_404(
        self, client, headers_aluno, matricula_aluno,
        prova_do_modulo
    ):
        """Resultado sem ter respondido retorna 404"""
        response = client.get(
            f"/api/v1/provas/{prova_do_modulo.id}/resultado",
            headers=headers_aluno
        )
        assert response.status_code == 404

    def test_resultado_sem_matricula_retorna_403(
        self, client, headers_aluno, prova_do_modulo,
        curso_publicado_simples, modulo_do_curso_publicado
    ):
        """Aluno não matriculado não acessa resultado"""
        response = client.get(
            f"/api/v1/provas/{prova_do_modulo.id}/resultado",
            headers=headers_aluno
        )
        assert response.status_code == 403

    def test_responder_prova_incompleta_retorna_400(
        self, client, headers_aluno, matricula_aluno,
        curso_publicado_simples, modulo_do_curso_publicado, prova_do_modulo,
        db_session
    ):
        """Submissão sem responder todas as perguntas retorna 400"""
        # Enviar lista vazia
        body = []
        response = client.post(
            f"/api/v1/provas/{prova_do_modulo.id}/responder",
            json=body,
            headers=headers_aluno
        )
        assert response.status_code == 400
