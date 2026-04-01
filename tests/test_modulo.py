import pytest


class TestCriarModulo:
    """Testes para criação de módulos (RF18, RF19)"""

    def test_criar_modulo_com_sucesso(self, client, headers_professor, curso_professor):
        """Teste: Criar módulo com nome automático Módulo 01 (RF19)"""
        response = client.post(
            f"/api/v1/cursos/{curso_professor.id}/modulos",
            headers=headers_professor
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nome"] == "Módulo 01"
        assert data["ordem"] == 1

    def test_criar_segundo_modulo_incrementa_nome(self, client, headers_professor, curso_professor):
        """Teste: Segundo módulo recebe nome 'Módulo 02' (RF19)"""
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        response = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nome"] == "Módulo 02"
        assert data["ordem"] == 2

    def test_criar_modulo_curso_inexistente(self, client, headers_professor):
        """Teste: Criar módulo em curso inexistente retorna 404"""
        response = client.post("/api/v1/cursos/9999/modulos", headers=headers_professor)
        assert response.status_code == 404

    def test_criar_modulo_curso_de_outro_professor(self, client, headers_professor, db_session):
        """Teste: Não permite criar módulo em curso de outro professor"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil
        from br.ufc.llm.curso.domain.curso import Curso

        outro = Usuario(nome="Outro Prof", cpf="44444444444", email="outro4@example.com", senha=SenhaUtil.hash_senha("senha123456"), perfil="PROFESSOR", status="ATIVO")
        db_session.add(outro)
        db_session.commit()

        curso = Curso(titulo="Curso do Outro", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=outro.id)
        db_session.add(curso)
        db_session.commit()

        response = client.post(f"/api/v1/cursos/{curso.id}/modulos", headers=headers_professor)
        assert response.status_code == 403

    def test_criar_modulo_sem_autenticacao(self, client, curso_professor):
        """Teste: Criar módulo sem autenticação retorna 401"""
        response = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos")
        assert response.status_code == 401


class TestListarModulos:
    """Testes para listagem de módulos"""

    def test_listar_modulos_curso(self, client, headers_professor, curso_professor):
        """Teste: Listar módulos de um curso"""
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        response = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["modulos"]) == 2

    def test_listar_modulos_em_ordem(self, client, headers_professor, curso_professor):
        """Teste: Módulos listados em ordem crescente"""
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        response = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        assert response.status_code == 200
        modulos = response.json()["data"]["modulos"]
        assert modulos[0]["ordem"] == 1
        assert modulos[1]["ordem"] == 2
        assert modulos[2]["ordem"] == 3


class TestObterModulo:
    """Testes para obter módulo por ID"""

    def test_obter_modulo_com_sucesso(self, client, headers_professor, curso_professor):
        """Teste: Obter módulo por ID"""
        post_resp = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        modulo_id = post_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos/{modulo_id}", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Módulo 01"

    def test_obter_modulo_nao_encontrado(self, client, headers_professor, curso_professor):
        """Teste: Módulo inexistente retorna 404"""
        response = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos/9999", headers=headers_professor)
        assert response.status_code == 404


class TestEditarModulo:
    """Testes para edição de módulos"""

    def test_editar_nome_modulo(self, client, headers_professor, curso_professor):
        """Teste: Editar nome do módulo"""
        post_resp = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        modulo_id = post_resp.json()["data"]["id"]

        response = client.put(
            f"/api/v1/cursos/{curso_professor.id}/modulos/{modulo_id}",
            json={"nome": "Introdução ao Python"},
            headers=headers_professor
        )

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Introdução ao Python"


class TestDeletarModulo:
    """Testes para deleção de módulos (RF20)"""

    def test_deletar_modulo_renumera(self, client, headers_professor, curso_professor):
        """Teste: Ao deletar módulo do meio, os demais são renumerados (RF20)"""
        r1 = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        r2 = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        r3 = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)

        modulo2_id = r2.json()["data"]["id"]

        # Deletar o segundo módulo
        response = client.delete(f"/api/v1/cursos/{curso_professor.id}/modulos/{modulo2_id}", headers=headers_professor)
        assert response.status_code == 200

        # Listar e verificar renumeração
        lista = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        modulos = lista.json()["data"]["modulos"]

        assert len(modulos) == 2
        assert modulos[0]["nome"] == "Módulo 01"
        assert modulos[0]["ordem"] == 1
        assert modulos[1]["nome"] == "Módulo 02"
        assert modulos[1]["ordem"] == 2

    def test_deletar_modulo_unico(self, client, headers_professor, curso_professor):
        """Teste: Deletar único módulo com sucesso"""
        r = client.post(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        modulo_id = r.json()["data"]["id"]

        response = client.delete(f"/api/v1/cursos/{curso_professor.id}/modulos/{modulo_id}", headers=headers_professor)
        assert response.status_code == 200

        lista = client.get(f"/api/v1/cursos/{curso_professor.id}/modulos", headers=headers_professor)
        assert len(lista.json()["data"]["modulos"]) == 0
