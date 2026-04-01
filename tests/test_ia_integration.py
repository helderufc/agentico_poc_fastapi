"""
Testes de integração real com OpenAI GPT-4o.
Chamam a API de verdade — requerem OPENAI_API_KEY no .env.

Executar com:
    pytest -m integration
"""
import pytest
from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.modulo.domain.modulo import Modulo


# ===========================================================================
# RF26: Geração de conteúdo de aula — chamada real
# ===========================================================================

@pytest.mark.integration
class TestGerarConteudoAulaReal:

    def test_gera_html_a_partir_de_ck_editor(self, client, headers_professor, modulo, db_session):
        """GPT-4o retorna HTML com base no conteúdo CKEditor"""
        aula = Aula(
            nome="Introdução ao Python",
            ordem=50,
            conteudo_ck_editor=(
                "<p>Python é uma linguagem interpretada de alto nível. "
                "É amplamente usada em ciência de dados, web e automação.</p>"
            ),
            modulo_id=modulo.id
        )
        db_session.add(aula)
        db_session.commit()

        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo",
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "conteudo_gerado" in data
        assert len(data["conteudo_gerado"]) > 50
        # Deve retornar HTML
        assert "<" in data["conteudo_gerado"]

    def test_conteudo_gerado_nao_salvo_automaticamente(
        self, client, headers_professor, modulo, db_session
    ):
        """RF27: campo conteudo_gerado permanece None após gerar"""
        aula = Aula(
            nome="Aula Verificação RF27",
            ordem=51,
            conteudo_ck_editor="<p>Conteúdo sobre variáveis em Python.</p>",
            modulo_id=modulo.id
        )
        db_session.add(aula)
        db_session.commit()

        client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo",
            headers=headers_professor
        )

        db_session.refresh(aula)
        assert aula.conteudo_gerado is None

    def test_confirmar_persiste_conteudo(self, client, headers_professor, modulo, db_session):
        """RF28: confirmar-conteudo salva no banco de verdade"""
        aula = Aula(
            nome="Aula Confirmar RF28",
            ordem=52,
            conteudo_ck_editor="<p>Loops em Python: for e while.</p>",
            modulo_id=modulo.id
        )
        db_session.add(aula)
        db_session.commit()

        # Gerar
        r_gerar = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo",
            headers=headers_professor
        )
        assert r_gerar.status_code == 200
        html_gerado = r_gerar.json()["data"]["conteudo_gerado"]

        # Confirmar
        r_confirmar = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/confirmar-conteudo",
            json={"conteudo_gerado": html_gerado},
            headers=headers_professor
        )
        assert r_confirmar.status_code == 200

        db_session.refresh(aula)
        assert aula.conteudo_gerado == html_gerado


# ===========================================================================
# RF35: Geração de quiz — chamada real
# ===========================================================================

@pytest.mark.integration
class TestGerarQuizIAReal:

    def test_gera_quiz_com_perguntas_e_alternativas(
        self, client, headers_professor, curso_professor, db_session
    ):
        """RF35: GPT-4o retorna perguntas com alternativas válidas"""
        modulo = Modulo(nome="Módulo IA Real", ordem=50, curso_id=curso_professor.id)
        db_session.add(modulo)
        db_session.commit()

        aula = Aula(
            nome="Aula IA Real",
            ordem=1,
            conteudo_ck_editor=(
                "<p>Orientação a objetos em Python: classes, herança, encapsulamento e polimorfismo. "
                "Uma classe define atributos e métodos. Herança permite reutilizar código. "
                "Encapsulamento protege o estado interno. Polimorfismo permite comportamentos distintos.</p>"
            ),
            modulo_id=modulo.id
        )
        db_session.add(aula)
        db_session.commit()

        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "perguntas" in data
        assert len(data["perguntas"]) >= 1

        for pergunta in data["perguntas"]:
            assert "enunciado" in pergunta
            assert len(pergunta["alternativas"]) >= 2
            corretas = [a for a in pergunta["alternativas"] if a["correta"]]
            assert len(corretas) == 1, "Cada pergunta deve ter exatamente 1 alternativa correta"

    def test_quiz_nao_persiste_no_banco(
        self, client, headers_professor, curso_professor, db_session
    ):
        """RF36: Quiz gerado não cria prova no banco"""
        from br.ufc.llm.prova.domain.prova import Prova

        modulo = Modulo(nome="Módulo Sem Prova", ordem=51, curso_id=curso_professor.id)
        db_session.add(modulo)
        db_session.commit()

        aula = Aula(
            nome="Aula Conteúdo",
            ordem=1,
            conteudo_ck_editor="<p>Funções em Python: def, return, parâmetros, *args e **kwargs.</p>",
            modulo_id=modulo.id
        )
        db_session.add(aula)
        db_session.commit()

        client.post(
            f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
            headers=headers_professor
        )

        prova = db_session.query(Prova).filter(Prova.modulo_id == modulo.id).first()
        assert prova is None

    def test_quiz_modulo_sem_conteudo_retorna_422(
        self, client, headers_professor, curso_professor, db_session
    ):
        """RF37: Módulo sem aulas com conteúdo retorna 422"""
        modulo = Modulo(nome="Módulo Vazio Real", ordem=52, curso_id=curso_professor.id)
        db_session.add(modulo)
        db_session.commit()

        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
            headers=headers_professor
        )
        assert response.status_code == 422
