import pytest


class TestCriarAula:
    """Testes para criação de aulas (RF22)"""

    def test_criar_aula_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Criar aula simples com nome"""
        dados = {"nome": "Aula 1: Introdução"}
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nome"] == "Aula 1: Introdução"
        assert data["ordem"] == 1

    def test_criar_aula_com_conteudo_ck_editor(self, client, headers_professor, modulo):
        """Teste: Criar aula com conteúdo HTML (RF24)"""
        dados = {
            "nome": "Aula com conteúdo",
            "conteudo_ck_editor": "<p>Olá <b>mundo</b>!</p><script>alert('xss')</script>"
        }
        response = client.post(
            f"/api/v1/modulos/{modulo.id}/aulas",
            json=dados,
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        # Script deve ser removido por sanitização bleach
        assert "<script>" not in data["conteudo_ck_editor"]
        assert "<p>" in data["conteudo_ck_editor"]

    def test_criar_segunda_aula_incrementa_ordem(self, client, headers_professor, modulo):
        """Teste: Segunda aula recebe ordem 2"""
        client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula 1"}, headers=headers_professor)
        response = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula 2"}, headers=headers_professor)

        assert response.status_code == 201
        assert response.json()["data"]["ordem"] == 2

    def test_criar_aula_modulo_inexistente(self, client, headers_professor):
        """Teste: Criar aula em módulo inexistente retorna 404"""
        dados = {"nome": "Aula Órfã"}
        response = client.post("/api/v1/modulos/9999/aulas", json=dados, headers=headers_professor)
        assert response.status_code == 404

    def test_criar_aula_sem_autenticacao(self, client, modulo):
        """Teste: Criar aula sem token retorna 401"""
        response = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula"})
        assert response.status_code == 401


class TestListarAulas:
    """Testes para listagem de aulas"""

    def test_listar_aulas_modulo(self, client, headers_professor, modulo):
        """Teste: Listar aulas de um módulo"""
        client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula 1"}, headers=headers_professor)
        client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula 2"}, headers=headers_professor)

        response = client.get(f"/api/v1/modulos/{modulo.id}/aulas", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["aulas"]) == 2

    def test_listar_aulas_em_ordem(self, client, headers_professor, modulo):
        """Teste: Aulas listadas em ordem crescente de 'ordem'"""
        client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula A"}, headers=headers_professor)
        client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula B"}, headers=headers_professor)

        response = client.get(f"/api/v1/modulos/{modulo.id}/aulas", headers=headers_professor)
        aulas = response.json()["data"]["aulas"]

        assert aulas[0]["ordem"] == 1
        assert aulas[1]["ordem"] == 2


class TestObterAula:
    """Testes para obter aula por ID"""

    def test_obter_aula_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Obter aula pelo ID"""
        r = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Minha Aula"}, headers=headers_professor)
        aula_id = r.json()["data"]["id"]

        response = client.get(f"/api/v1/modulos/{modulo.id}/aulas/{aula_id}", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Minha Aula"

    def test_obter_aula_nao_encontrada(self, client, headers_professor, modulo):
        """Teste: Aula inexistente retorna 404"""
        response = client.get(f"/api/v1/modulos/{modulo.id}/aulas/9999", headers=headers_professor)
        assert response.status_code == 404


class TestEditarAula:
    """Testes para edição de aulas (RF24)"""

    def test_editar_aula_sanitiza_html(self, client, headers_professor, modulo):
        """Teste: Editar aula sanitiza conteudo_ck_editor com bleach (RF24)"""
        r = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Aula para editar"}, headers=headers_professor)
        aula_id = r.json()["data"]["id"]

        dados = {
            "nome": "Aula Editada",
            "conteudo_ck_editor": "<p>Conteúdo</p><script>alert('xss')</script><b>Negrito</b>"
        }
        response = client.put(f"/api/v1/modulos/{modulo.id}/aulas/{aula_id}", json=dados, headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert "<script>" not in data["conteudo_ck_editor"]
        assert "<b>" in data["conteudo_ck_editor"] or "Negrito" in data["conteudo_ck_editor"]

    def test_editar_aula_nome(self, client, headers_professor, modulo):
        """Teste: Editar nome da aula"""
        r = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Nome Antigo"}, headers=headers_professor)
        aula_id = r.json()["data"]["id"]

        response = client.put(f"/api/v1/modulos/{modulo.id}/aulas/{aula_id}", json={"nome": "Nome Novo"}, headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Nome Novo"


class TestDeletarAula:
    """Testes para deleção de aulas"""

    def test_deletar_aula_com_sucesso(self, client, headers_professor, modulo):
        """Teste: Deletar aula com sucesso"""
        r = client.post(f"/api/v1/modulos/{modulo.id}/aulas", json={"nome": "Para Deletar"}, headers=headers_professor)
        aula_id = r.json()["data"]["id"]

        response = client.delete(f"/api/v1/modulos/{modulo.id}/aulas/{aula_id}", headers=headers_professor)

        assert response.status_code == 200
        # Verificar que foi deletada
        r2 = client.get(f"/api/v1/modulos/{modulo.id}/aulas/{aula_id}", headers=headers_professor)
        assert r2.status_code == 404
