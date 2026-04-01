import pytest


class TestCriarCurso:
    """Testes para criação de cursos (RF09)"""

    def test_criar_curso_com_sucesso(self, client, headers_professor):
        """Teste: Professor cria curso com sucesso"""
        dados = {
            "titulo": "Python para Iniciantes",
            "categoria": "programacao",
            "descricao": "Curso completo de Python do zero ao avançado",
            "carga_horaria": "40h",
            "requer_endereco": False,
            "requer_genero": False,
            "requer_idade": False
        }
        response = client.post("/api/v1/cursos", json=dados, headers=headers_professor)

        assert response.status_code == 201
        assert response.json()["status"] == 201
        data = response.json()["data"]
        assert data["titulo"] == "Python para Iniciantes"
        assert data["status"] == "RASCUNHO"
        assert data["categoria"] == "PROGRAMACAO"  # RF11: salva em uppercase

    def test_criar_curso_categoria_uppercase(self, client, headers_professor):
        """Teste: Categoria salva em uppercase (RF11)"""
        dados = {
            "titulo": "Curso de Django",
            "categoria": "web development",
            "descricao": "Aprenda Django Framework",
            "carga_horaria": "20h"
        }
        response = client.post("/api/v1/cursos", json=dados, headers=headers_professor)

        assert response.status_code == 201
        assert response.json()["data"]["categoria"] == "WEB DEVELOPMENT"

    def test_criar_curso_sem_autenticacao(self, client):
        """Teste: Criar curso sem token retorna 401"""
        dados = {
            "titulo": "Curso Sem Auth",
            "categoria": "teste",
            "descricao": "Descricao",
            "carga_horaria": "10h"
        }
        response = client.post("/api/v1/cursos", json=dados)

        assert response.status_code == 401

    def test_criar_curso_status_inicial_rascunho(self, client, headers_professor):
        """Teste: Status inicial é RASCUNHO (RF14)"""
        dados = {
            "titulo": "Curso Novo",
            "categoria": "dados",
            "descricao": "Descricao do curso",
            "carga_horaria": "15h"
        }
        response = client.post("/api/v1/cursos", json=dados, headers=headers_professor)

        assert response.status_code == 201
        assert response.json()["data"]["status"] == "RASCUNHO"


class TestListarCursos:
    """Testes para listagem de cursos (RF15)"""

    def test_listar_cursos_professor(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor lista apenas seus próprios cursos"""
        from br.ufc.llm.curso.domain.curso import Curso

        # Criar curso diretamente no banco
        curso = Curso(
            titulo="Meu Curso",
            categoria="TI",
            descricao="Descrição",
            carga_horaria="10h",
            professor_id=usuario_professor.id
        )
        db_session.add(curso)
        db_session.commit()

        response = client.get("/api/v1/cursos", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["cursos"]) == 1
        assert data["cursos"][0]["titulo"] == "Meu Curso"

    def test_listar_cursos_filtrar_por_status(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Filtrar cursos por status (RF15)"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso_rascunho = Curso(titulo="Rascunho", categoria="TI", descricao="Desc", carga_horaria="1h", professor_id=usuario_professor.id, status="RASCUNHO")
        curso_publicado = Curso(titulo="Publicado", categoria="TI", descricao="Desc", carga_horaria="1h", professor_id=usuario_professor.id, status="PUBLICADO")
        db_session.add_all([curso_rascunho, curso_publicado])
        db_session.commit()

        response = client.get("/api/v1/cursos?status=PUBLICADO", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["cursos"]) == 1
        assert data["cursos"][0]["status"] == "PUBLICADO"

    def test_listar_cursos_busca_por_texto(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Busca por título ou categoria (RF17)"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Machine Learning Avançado", categoria="IA", descricao="Desc", carga_horaria="50h", professor_id=usuario_professor.id)
        db_session.add(curso)
        db_session.commit()

        response = client.get("/api/v1/cursos?q=machine", headers=headers_professor)

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["cursos"]) == 1
        assert "Machine Learning" in data["cursos"][0]["titulo"]

    def test_listar_cursos_sem_autenticacao(self, client):
        """Teste: Listar sem autenticação retorna 401"""
        response = client.get("/api/v1/cursos")
        assert response.status_code == 401


class TestObterCurso:
    """Testes para obter curso por ID"""

    def test_obter_curso_com_sucesso(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor obtém seu próprio curso"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Meu Curso", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=usuario_professor.id)
        db_session.add(curso)
        db_session.commit()

        response = client.get(f"/api/v1/cursos/{curso.id}", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["titulo"] == "Meu Curso"

    def test_obter_curso_nao_encontrado(self, client, headers_professor):
        """Teste: Curso inexistente retorna 404"""
        response = client.get("/api/v1/cursos/9999", headers=headers_professor)
        assert response.status_code == 404

    def test_obter_curso_de_outro_professor(self, client, headers_professor, db_session):
        """Teste: Professor não acessa curso de outro (RF09)"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil
        from br.ufc.llm.curso.domain.curso import Curso

        outro = Usuario(nome="Outro Prof", cpf="11111111111", email="outro@example.com", senha=SenhaUtil.hash_senha("senha123456"), perfil="PROFESSOR", status="ATIVO")
        db_session.add(outro)
        db_session.commit()

        curso = Curso(titulo="Curso do Outro", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=outro.id)
        db_session.add(curso)
        db_session.commit()

        response = client.get(f"/api/v1/cursos/{curso.id}", headers=headers_professor)
        assert response.status_code == 403


class TestEditarCurso:
    """Testes para edição de cursos (RF16)"""

    def test_editar_curso_com_sucesso(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor edita seu próprio curso"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Título Antigo", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=usuario_professor.id)
        db_session.add(curso)
        db_session.commit()

        dados = {"titulo": "Título Novo", "categoria": "TECNOLOGIA", "descricao": "Nova descrição", "carga_horaria": "20h"}
        response = client.put(f"/api/v1/cursos/{curso.id}", json=dados, headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["titulo"] == "Título Novo"

    def test_editar_curso_de_outro_professor(self, client, headers_professor, db_session):
        """Teste: Não permite editar curso de outro professor"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil
        from br.ufc.llm.curso.domain.curso import Curso

        outro = Usuario(nome="Outro Prof", cpf="22222222222", email="outro2@example.com", senha=SenhaUtil.hash_senha("senha123456"), perfil="PROFESSOR", status="ATIVO")
        db_session.add(outro)
        db_session.commit()

        curso = Curso(titulo="Curso do Outro", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=outro.id)
        db_session.add(curso)
        db_session.commit()

        dados = {"titulo": "Hackado", "categoria": "TI", "descricao": "Desc", "carga_horaria": "1h"}
        response = client.put(f"/api/v1/cursos/{curso.id}", json=dados, headers=headers_professor)
        assert response.status_code == 403


class TestDeletarCurso:
    """Testes para deleção de cursos"""

    def test_deletar_curso_com_sucesso(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor deleta seu próprio curso"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Para Deletar", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=usuario_professor.id)
        db_session.add(curso)
        db_session.commit()
        curso_id = curso.id

        response = client.delete(f"/api/v1/cursos/{curso_id}", headers=headers_professor)

        assert response.status_code == 200
        # Verificar que o curso foi deletado
        response2 = client.get(f"/api/v1/cursos/{curso_id}", headers=headers_professor)
        assert response2.status_code == 404

    def test_deletar_curso_de_outro_professor(self, client, headers_professor, db_session):
        """Teste: Não permite deletar curso de outro professor"""
        from br.ufc.llm.usuario.domain.usuario import Usuario
        from br.ufc.llm.shared.domain.seguranca import SenhaUtil
        from br.ufc.llm.curso.domain.curso import Curso

        outro = Usuario(nome="Outro Prof", cpf="33333333333", email="outro3@example.com", senha=SenhaUtil.hash_senha("senha123456"), perfil="PROFESSOR", status="ATIVO")
        db_session.add(outro)
        db_session.commit()

        curso = Curso(titulo="Curso Protegido", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=outro.id)
        db_session.add(curso)
        db_session.commit()

        response = client.delete(f"/api/v1/cursos/{curso.id}", headers=headers_professor)
        assert response.status_code == 403


class TestStatusCurso:
    """Testes para mudança de status de cursos (RF14)"""

    def test_publicar_curso(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor publica curso"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Para Publicar", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=usuario_professor.id, status="RASCUNHO")
        db_session.add(curso)
        db_session.commit()

        response = client.patch(f"/api/v1/cursos/{curso.id}/publicar", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "PUBLICADO"

    def test_arquivar_curso(self, client, headers_professor, usuario_professor, db_session):
        """Teste: Professor arquiva curso"""
        from br.ufc.llm.curso.domain.curso import Curso

        curso = Curso(titulo="Para Arquivar", categoria="TI", descricao="Desc", carga_horaria="10h", professor_id=usuario_professor.id, status="PUBLICADO")
        db_session.add(curso)
        db_session.commit()

        response = client.patch(f"/api/v1/cursos/{curso.id}/arquivar", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ARQUIVADO"
