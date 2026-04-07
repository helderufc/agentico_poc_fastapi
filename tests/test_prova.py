import pytest


class TestCriarProva:
    """Testes para criação de provas (RF29)"""

    def test_criar_prova_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Criar prova vinculada a módulo"""
        dados = {
            "mostrar_respostas_erradas": True,
            "mostrar_respostas_corretas": False,
            "mostrar_valores": True
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["mostrar_respostas_erradas"] == True
        assert data["mostrar_valores"] == True
        assert data["modulo_id"] == modulo.id

    def test_criar_prova_modulo_inexistente(self, client, headers_professor):
        """Teste: Criar prova em módulo inexistente retorna 404"""
        response = client.post("/api/v1/modulos/9999/prova", json={}, headers=headers_professor)
        assert response.status_code == 404

    def test_criar_prova_duplicada_retorna_erro(self, client, headers_professor, modulo):
        """Teste: Módulo só pode ter uma prova"""
        client.post(f"/api/v1/modulos/{modulo.id}/prova", json={}, headers=headers_professor)
        response = client.post(f"/api/v1/modulos/{modulo.id}/prova", json={}, headers=headers_professor)

        assert response.status_code == 400

    def test_criar_prova_sem_autenticacao(self, client, modulo):
        """Teste: Criar prova sem token retorna 401"""
        response = client.post(f"/api/v1/modulos/{modulo.id}/prova", json={})
        assert response.status_code == 401


class TestObterProva:
    """Testes para obter prova"""

    def test_obter_prova_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Obter prova com perguntas"""
        client.post(f"/api/v1/modulos/{modulo.id}/prova", json={}, headers=headers_professor)

        response = client.get(f"/api/v1/modulos/{modulo.id}/prova", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["modulo_id"] == modulo.id
        assert "perguntas" in data

    def test_obter_prova_inexistente(self, client, headers_professor, modulo):
        """Teste: Módulo sem prova retorna 404"""
        response = client.get(f"/api/v1/modulos/{modulo.id}/prova", headers=headers_professor)
        assert response.status_code == 404


class TestEditarProva:
    """Testes para edição de configurações da prova (RF32-RF33)"""

    def test_editar_configuracoes_prova(self, client, headers_professor, modulo):
        """Teste: Editar configurações da prova"""
        client.post(f"/api/v1/modulos/{modulo.id}/prova", json={}, headers=headers_professor)

        dados = {
            "mostrar_respostas_erradas": True,
            "mostrar_respostas_corretas": True,
            "mostrar_valores": False
        }
        response = client.put(f"/api/v1/modulos/{modulo.id}/prova", json=dados, headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["mostrar_respostas_erradas"] == True
        assert data["mostrar_respostas_corretas"] == True
        assert data["mostrar_valores"] == False


class TestDeletarProva:
    """Testes para deleção de prova"""

    def test_deletar_prova_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Deletar prova com sucesso"""
        client.post(f"/api/v1/modulos/{modulo.id}/prova", json={}, headers=headers_professor)

        response = client.delete(f"/api/v1/modulos/{modulo.id}/prova", headers=headers_professor)
        assert response.status_code == 200

        # Verificar que foi deletada
        r2 = client.get(f"/api/v1/modulos/{modulo.id}/prova", headers=headers_professor)
        assert r2.status_code == 404


class TestAdicionarPergunta:
    """Testes para adicionar perguntas (RF30-RF31)"""

    def test_adicionar_pergunta_com_sucesso(self, client, headers_professor, prova):
        """Teste: Adicionar pergunta com mínimo 2 alternativas e 1 correta"""
        dados = {
            "enunciado": "Qual é a capital do Brasil?",
            "pontos": 2,
            "alternativas": [
                {"texto": "São Paulo", "correta": False},
                {"texto": "Brasília", "correta": True},
                {"texto": "Rio de Janeiro", "correta": False}
            ]
        }
        response = client.post(
            f"/api/v1/provas/{prova.id}/perguntas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["enunciado"] == "Qual é a capital do Brasil?"
        assert data["pontos"] == 2
        assert len(data["alternativas"]) == 3

    def test_adicionar_pergunta_ponto_default(self, client, headers_professor, prova):
        """Teste: Pontos padrão é 1 (RF31)"""
        dados = {
            "enunciado": "Pergunta padrão?",
            "alternativas": [
                {"texto": "Opção A", "correta": True},
                {"texto": "Opção B", "correta": False}
            ]
        }
        response = client.post(
            f"/api/v1/provas/{prova.id}/perguntas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        assert response.json()["data"]["pontos"] == 1

    def test_adicionar_pergunta_menos_de_duas_alternativas(self, client, headers_professor, prova):
        """Teste: Mínimo 2 alternativas (RF30) — retorna 400 ou 422"""
        dados = {
            "enunciado": "Pergunta inválida?",
            "alternativas": [
                {"texto": "Única opção", "correta": True}
            ]
        }
        response = client.post(
            f"/api/v1/provas/{prova.id}/perguntas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code in (400, 422)

    def test_adicionar_pergunta_sem_alternativa_correta(self, client, headers_professor, prova):
        """Teste: Exatamente 1 alternativa correta (RF30)"""
        dados = {
            "enunciado": "Pergunta sem correta?",
            "alternativas": [
                {"texto": "Opção A", "correta": False},
                {"texto": "Opção B", "correta": False}
            ]
        }
        response = client.post(
            f"/api/v1/provas/{prova.id}/perguntas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 400

    def test_adicionar_pergunta_mais_de_uma_correta(self, client, headers_professor, prova):
        """Teste: Não pode ter mais de 1 alternativa correta (RF30)"""
        dados = {
            "enunciado": "Pergunta com duas corretas?",
            "alternativas": [
                {"texto": "Opção A", "correta": True},
                {"texto": "Opção B", "correta": True}
            ]
        }
        response = client.post(
            f"/api/v1/provas/{prova.id}/perguntas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 400

    def test_adicionar_pergunta_prova_inexistente(self, client, headers_professor):
        """Teste: Adicionar pergunta em prova inexistente retorna 404"""
        dados = {
            "enunciado": "Pergunta?",
            "alternativas": [
                {"texto": "A", "correta": True},
                {"texto": "B", "correta": False}
            ]
        }
        response = client.post("/api/v1/provas/9999/perguntas", json=dados, headers=headers_professor)
        assert response.status_code == 404


class TestEditarPergunta:
    """Testes para edição de perguntas"""

    def test_editar_pergunta_com_sucesso(self, client, headers_professor, prova):
        """Teste: Editar enunciado e alternativas da pergunta"""
        # Adicionar pergunta
        dados = {
            "enunciado": "Pergunta original",
            "alternativas": [
                {"texto": "A", "correta": True},
                {"texto": "B", "correta": False}
            ]
        }
        r = client.post(f"/api/v1/provas/{prova.id}/perguntas", json=dados, headers=headers_professor)
        pergunta_id = r.json()["data"]["id"]

        novos_dados = {
            "enunciado": "Pergunta editada",
            "pontos": 5,
            "alternativas": [
                {"texto": "Nova A", "correta": False},
                {"texto": "Nova B", "correta": True}
            ]
        }
        response = client.put(f"/api/v1/provas/{prova.id}/perguntas/{pergunta_id}", json=novos_dados, headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["enunciado"] == "Pergunta editada"
        assert data["pontos"] == 5


class TestDeletarPergunta:
    """Testes para deleção de perguntas"""

    def test_deletar_pergunta_com_sucesso(self, client, headers_professor, prova):
        """Teste: Deletar pergunta da prova"""
        dados = {
            "enunciado": "Para deletar",
            "alternativas": [
                {"texto": "A", "correta": True},
                {"texto": "B", "correta": False}
            ]
        }
        r = client.post(f"/api/v1/provas/{prova.id}/perguntas", json=dados, headers=headers_professor)
        pergunta_id = r.json()["data"]["id"]

        response = client.delete(f"/api/v1/provas/{prova.id}/perguntas/{pergunta_id}", headers=headers_professor)

        assert response.status_code == 200


class TestEstatisticasProva:
    """Testes para estatísticas de respostas da prova (RF34)"""

    def test_estatisticas_sem_respostas(self, client, headers_professor, modulo, prova):
        """Prova sem respostas ainda retorna contadores zerados"""
        # Adicionar pergunta à prova
        dados = {
            "enunciado": "Quanto é 2+2?",
            "alternativas": [
                {"texto": "3", "correta": False},
                {"texto": "4", "correta": True}
            ]
        }
        client.post(f"/api/v1/provas/{prova.id}/perguntas", json=dados, headers=headers_professor)

        response = client.get(
            f"/api/v1/modulos/{modulo.id}/prova/estatisticas",
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_respondentes"] == 0
        assert len(data["perguntas"]) >= 1
        assert all(
            a["total_respostas"] == 0
            for p in data["perguntas"]
            for a in p["alternativas"]
        )

    def test_estatisticas_com_respostas(
        self, client, headers_professor, headers_aluno,
        modulo, prova, db_session, usuario_aluno, curso_professor
    ):
        """Estatísticas refletem respostas dos alunos"""
        from br.ufc.llm.prova.domain.prova import Pergunta, Alternativa
        from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva

        # Adicionar pergunta com 2 alternativas
        pergunta = Pergunta(enunciado="Pergunta stat?", pontos=1, ordem=1, prova_id=prova.id)
        db_session.add(pergunta)
        db_session.commit()
        db_session.refresh(pergunta)

        alt_a = Alternativa(texto="A", correta=True, pergunta_id=pergunta.id)
        alt_b = Alternativa(texto="B", correta=False, pergunta_id=pergunta.id)
        db_session.add_all([alt_a, alt_b])
        db_session.commit()
        db_session.refresh(alt_a)
        db_session.refresh(alt_b)

        # Matricular e registrar resposta do aluno
        matricula = Matricula(aluno_id=usuario_aluno.id, curso_id=curso_professor.id)
        db_session.add(matricula)
        db_session.commit()

        resposta = RespostaProva(
            aluno_id=usuario_aluno.id,
            prova_id=prova.id,
            pergunta_id=pergunta.id,
            alternativa_id=alt_a.id
        )
        db_session.add(resposta)
        db_session.commit()

        response = client.get(
            f"/api/v1/modulos/{modulo.id}/prova/estatisticas",
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_respondentes"] == 1

        # Encontrar a pergunta que adicionamos
        pergunta_stat = next(p for p in data["perguntas"] if p["pergunta_id"] == pergunta.id)
        alternativas_stat = {a["alternativa_id"]: a for a in pergunta_stat["alternativas"]}
        assert alternativas_stat[alt_a.id]["total_respostas"] == 1
        assert alternativas_stat[alt_a.id]["percentual"] == 100.0
        assert alternativas_stat[alt_b.id]["total_respostas"] == 0
        assert alternativas_stat[alt_b.id]["percentual"] == 0.0

    def test_estatisticas_prova_inexistente_retorna_404(self, client, headers_professor, modulo):
        """Módulo sem prova retorna 404"""
        response = client.get(
            f"/api/v1/modulos/{modulo.id}/prova/estatisticas",
            headers=headers_professor
        )
        assert response.status_code == 404

    def test_estatisticas_sem_autenticacao_retorna_401(self, client, modulo, prova):
        """Sem token retorna 401"""
        response = client.get(f"/api/v1/modulos/{modulo.id}/prova/estatisticas")
        assert response.status_code == 401

    def test_estatisticas_acesso_negado_outro_professor(
        self, client, db_session, modulo, prova
    ):
        """Outro professor não acessa estatísticas do curso alheio"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil, JWTUtil

        outro = Usuario(
            nome="Outro Prof",
            cpf="99988877766",
            email="outro@example.com",
            senha=SenhaUtil.hash_senha("senha123456"),
            perfil="PROFESSOR",
            status="ATIVO"
        )
        db_session.add(outro)
        db_session.commit()

        tokens = JWTUtil.gerar_tokens(outro.id, outro.email, outro.perfil)
        headers_outro = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.get(
            f"/api/v1/modulos/{modulo.id}/prova/estatisticas",
            headers=headers_outro
        )
        assert response.status_code == 403

    def test_estrutura_resposta_estatisticas(self, client, headers_professor, modulo, prova):
        """Estrutura do response contém os campos esperados"""
        from br.ufc.llm.prova.domain.prova import Pergunta, Alternativa

        # Criar pergunta via conftest prova (já tem 1 pergunta) — verificar estrutura
        response = client.get(
            f"/api/v1/modulos/{modulo.id}/prova/estatisticas",
            headers=headers_professor
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_respondentes" in data
        assert "perguntas" in data
        assert "prova_id" in data


class TestCriarQuizManual:
    """Testes para criação de quiz completo manualmente em uma única requisição"""

    def test_criar_quiz_manual_com_sucesso(self, client, headers_professor, modulo):
        """Criar prova completa com perguntas e alternativas em uma única requisição"""
        dados = {
            "mostrar_respostas_erradas": True,
            "mostrar_respostas_corretas": False,
            "mostrar_valores": True,
            "perguntas": [
                {
                    "enunciado": "Qual é a capital do Brasil?",
                    "pontos": 2,
                    "alternativas": [
                        {"texto": "São Paulo", "correta": False},
                        {"texto": "Brasília", "correta": True},
                        {"texto": "Rio de Janeiro", "correta": False}
                    ]
                },
                {
                    "enunciado": "Quanto é 2+2?",
                    "pontos": 1,
                    "alternativas": [
                        {"texto": "3", "correta": False},
                        {"texto": "4", "correta": True}
                    ]
                }
            ]
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["mostrar_respostas_erradas"] == True
        assert data["mostrar_valores"] == True
        assert data["modulo_id"] == modulo.id
        assert len(data["perguntas"]) == 2
        assert data["perguntas"][0]["pontos"] == 2
        assert len(data["perguntas"][0]["alternativas"]) == 3

    def test_criar_quiz_manual_sem_perguntas(self, client, headers_professor, modulo):
        """Criar prova manual sem perguntas — aceita lista vazia"""
        dados = {"perguntas": []}
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json=dados,
            headers=headers_professor
        )
        assert response.status_code == 201
        assert response.json()["data"]["perguntas"] == []

    def test_criar_quiz_manual_modulo_inexistente(self, client, headers_professor):
        """Módulo inexistente retorna 404"""
        response = client.post(
            "/api/v1/modulos/9999/prova/manual",
            json={"perguntas": []},
            headers=headers_professor
        )
        assert response.status_code == 404

    def test_criar_quiz_manual_modulo_ja_tem_prova(self, client, headers_professor, modulo, prova):
        """Módulo que já possui prova retorna 400"""
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json={"perguntas": []},
            headers=headers_professor
        )
        assert response.status_code == 400

    def test_criar_quiz_manual_sem_autenticacao(self, client, modulo):
        """Sem token retorna 401"""
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json={"perguntas": []}
        )
        assert response.status_code == 401

    def test_criar_quiz_manual_pergunta_sem_correta(self, client, headers_professor, modulo):
        """Pergunta sem alternativa correta retorna 400"""
        dados = {
            "perguntas": [
                {
                    "enunciado": "Pergunta inválida?",
                    "alternativas": [
                        {"texto": "A", "correta": False},
                        {"texto": "B", "correta": False}
                    ]
                }
            ]
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json=dados,
            headers=headers_professor
        )
        assert response.status_code == 400

    def test_criar_quiz_manual_pergunta_mais_de_uma_correta(self, client, headers_professor, modulo):
        """Pergunta com mais de uma alternativa correta retorna 400"""
        dados = {
            "perguntas": [
                {
                    "enunciado": "Pergunta com duas corretas?",
                    "alternativas": [
                        {"texto": "A", "correta": True},
                        {"texto": "B", "correta": True}
                    ]
                }
            ]
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json=dados,
            headers=headers_professor
        )
        assert response.status_code == 400

    def test_criar_quiz_manual_acesso_negado_outro_professor(self, client, db_session, modulo):
        """Outro professor não cria quiz em módulo alheio retorna 403"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil, JWTUtil

        outro = Usuario(
            nome="Outro Prof",
            cpf="99988877766",
            email="outro_manual@example.com",
            senha=SenhaUtil.hash_senha("senha123456"),
            perfil="PROFESSOR",
            status="ATIVO"
        )
        db_session.add(outro)
        db_session.commit()

        tokens = JWTUtil.gerar_tokens(outro.id, outro.email, outro.perfil)
        headers_outro = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json={"perguntas": []},
            headers=headers_outro
        )
        assert response.status_code == 403

    def test_criar_quiz_manual_ordem_perguntas(self, client, headers_professor, modulo):
        """Perguntas são ordenadas sequencialmente (1, 2, 3...)"""
        dados = {
            "perguntas": [
                {
                    "enunciado": "Primeira?",
                    "alternativas": [
                        {"texto": "A", "correta": True},
                        {"texto": "B", "correta": False}
                    ]
                },
                {
                    "enunciado": "Segunda?",
                    "alternativas": [
                        {"texto": "A", "correta": False},
                        {"texto": "B", "correta": True}
                    ]
                }
            ]
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/prova/manual",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        perguntas = response.json()["data"]["perguntas"]
        assert perguntas[0]["ordem"] == 1
        assert perguntas[1]["ordem"] == 2
