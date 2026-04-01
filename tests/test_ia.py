"""
Testes de integração com IA (com mock do OpenAI)
RF26 – gerar-conteudo
RF27 – conteúdo não persiste automaticamente
RF28 – confirmar-conteudo persiste em conteudo_gerado
RF35 – gerar-quiz-ia
RF36 – quiz não persiste
RF37 – 422 quando módulo não tem conteúdo legível
"""
import pytest
from unittest.mock import patch, MagicMock


# ===========================================================================
# Helpers
# ===========================================================================

HTML_GERADO = "<h1>Aula Gerada</h1><p>Conteúdo produzido pela IA.</p>"

QUIZ_GERADO = [
    {
        "enunciado": "O que é Python?",
        "pontos": 1,
        "alternativas": [
            {"texto": "Uma cobra", "correta": False},
            {"texto": "Uma linguagem de programação", "correta": True},
            {"texto": "Um framework", "correta": False},
        ],
    }
]


def _mock_gerar_conteudo(texto_fonte):
    return HTML_GERADO


def _mock_gerar_quiz(texto_fonte, num_perguntas=5):
    return QUIZ_GERADO


# ===========================================================================
# RF26-RF28: Geração de conteúdo de aula
# ===========================================================================

class TestGerarConteudoAula:

    def test_gerar_conteudo_com_ck_editor(self, client, headers_professor, modulo, aula):
        """RF26: Gera HTML a partir do conteúdo CKEditor"""
        with patch(
            "br.ufc.llm.shared.service.openai_service.gerar_conteudo_aula",
            side_effect=_mock_gerar_conteudo
        ):
            response = client.post(
                f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo",
                headers=headers_professor
            )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["conteudo_gerado"] == HTML_GERADO

    def test_gerar_conteudo_nao_persiste_automaticamente(
        self, client, headers_professor, modulo, aula, db_session
    ):
        """RF27: Conteúdo gerado não é salvo automaticamente"""
        with patch(
            "br.ufc.llm.shared.service.openai_service.gerar_conteudo_aula",
            side_effect=_mock_gerar_conteudo
        ):
            client.post(
                f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo",
                headers=headers_professor
            )

        # Recarregar do banco — campo deve continuar None
        db_session.refresh(aula)
        assert aula.conteudo_gerado is None

    def test_confirmar_conteudo_persiste(self, client, headers_professor, modulo, aula, db_session):
        """RF28: confirmar-conteudo salva no campo conteudo_gerado"""
        body = {"conteudo_gerado": HTML_GERADO}
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/confirmar-conteudo",
            json=body,
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["conteudo_gerado"] == HTML_GERADO

        db_session.refresh(aula)
        assert aula.conteudo_gerado == HTML_GERADO

    def test_gerar_conteudo_sem_fonte_retorna_422(
        self, client, headers_professor, modulo, db_session
    ):
        """RF26: Aula sem PDF nem CKEditor retorna 422"""
        from br.ufc.llm.aula.domain.aula import Aula

        aula_vazia = Aula(nome="Aula Vazia", ordem=99, modulo_id=modulo.id)
        db_session.add(aula_vazia)
        db_session.commit()

        with patch("br.ufc.llm.shared.service.openai_service.gerar_conteudo_aula"):
            response = client.post(
                f"/api/v1/modulos/{modulo.id}/aulas/{aula_vazia.id}/gerar-conteudo",
                headers=headers_professor
            )

        assert response.status_code == 422

    def test_gerar_conteudo_aula_inexistente_retorna_404(
        self, client, headers_professor, modulo
    ):
        """Aula não encontrada retorna 404"""
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/9999/gerar-conteudo",
            headers=headers_professor
        )
        assert response.status_code == 404

    def test_gerar_conteudo_sem_autenticacao_retorna_401(self, client, modulo, aula):
        """Sem token retorna 401"""
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/gerar-conteudo"
        )
        assert response.status_code == 401

    def test_confirmar_conteudo_sem_autenticacao_retorna_401(self, client, modulo, aula):
        """Confirmar sem token retorna 401"""
        body = {"conteudo_gerado": HTML_GERADO}
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas/{aula.id}/confirmar-conteudo",
            json=body
        )
        assert response.status_code == 401


# ===========================================================================
# RF35-RF38: Geração de quiz via IA
# ===========================================================================

class TestGerarQuizIA:

    def test_gerar_quiz_com_conteudo(self, client, headers_professor, modulo, aula):
        """RF35: Gera quiz a partir do conteúdo do módulo"""
        with patch(
            "br.ufc.llm.shared.service.openai_service.gerar_quiz",
            side_effect=_mock_gerar_quiz
        ):
            response = client.post(
                f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
                headers=headers_professor
            )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "perguntas" in data
        assert len(data["perguntas"]) == 1
        assert data["perguntas"][0]["enunciado"] == "O que é Python?"
        assert len(data["perguntas"][0]["alternativas"]) == 3

    def test_quiz_nao_persiste(self, client, headers_professor, modulo, aula, db_session):
        """RF36: Quiz gerado não é persistido"""
        with patch(
            "br.ufc.llm.shared.service.openai_service.gerar_quiz",
            side_effect=_mock_gerar_quiz
        ):
            client.post(
                f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
                headers=headers_professor
            )

        from br.ufc.llm.prova.domain.prova import Prova
        prova = db_session.query(Prova).filter(Prova.modulo_id == modulo.id).first()
        assert prova is None

    def test_quiz_modulo_sem_conteudo_retorna_422(
        self, client, headers_professor, curso_professor, db_session
    ):
        """RF37: Módulo sem conteúdo legível retorna 422"""
        from br.ufc.llm.modulo.domain.modulo import Modulo

        modulo_vazio = Modulo(nome="Módulo Vazio", ordem=99, curso_id=curso_professor.id)
        db_session.add(modulo_vazio)
        db_session.commit()

        response = client.post(
            f"/api/v1/modulos/{modulo_vazio.id}/prova/gerar-quiz-ia",
            headers=headers_professor
        )
        assert response.status_code == 422

    def test_quiz_estrutura_alternativas(self, client, headers_professor, modulo, aula):
        """Alternativas incluem texto e flag correta"""
        with patch(
            "br.ufc.llm.shared.service.openai_service.gerar_quiz",
            side_effect=_mock_gerar_quiz
        ):
            response = client.post(
                f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia",
                headers=headers_professor
            )

        perguntas = response.json()["data"]["perguntas"]
        for alt in perguntas[0]["alternativas"]:
            assert "texto" in alt
            assert "correta" in alt

        corretas = [a for a in perguntas[0]["alternativas"] if a["correta"]]
        assert len(corretas) == 1

    def test_quiz_sem_autenticacao_retorna_401(self, client, modulo):
        """Sem token retorna 401"""
        response = client.post(f"/api/v1/modulos/{modulo.id}/prova/gerar-quiz-ia")
        assert response.status_code == 401

    def test_quiz_modulo_inexistente_retorna_404(self, client, headers_professor):
        """Módulo inexistente retorna 404"""
        response = client.post(
            "/api/v1/modulos/9999/prova/gerar-quiz-ia",
            headers=headers_professor
        )
        assert response.status_code == 404
