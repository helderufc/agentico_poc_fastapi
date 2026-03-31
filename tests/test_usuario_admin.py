import pytest


class TestAdminUsuario:
    """Testes para funcionalidades de admin (RF04)"""

    def test_listar_usuarios_como_admin(self, client, headers_admin, usuario_professor, usuario_aluno):
        """Teste: Admin pode listar todos os usuários"""
        response = client.get("/api/v1/admin/usuarios", headers=headers_admin)

        assert response.status_code == 200
        assert "usuarios" in response.json()["data"]
        assert response.json()["data"]["total"] >= 2

    def test_listar_usuarios_sem_admin(self, client, headers_professor):
        """Teste: Não-admin não pode listar usuários"""
        response = client.get("/api/v1/admin/usuarios", headers=headers_professor)

        assert response.status_code == 403
        assert "administrador" in response.json()["detail"].lower()

    def test_listar_usuarios_paginado(self, client, headers_admin):
        """Teste: Listagem de usuários é paginada"""
        response = client.get("/api/v1/admin/usuarios?skip=0&limit=10", headers=headers_admin)

        assert response.status_code == 200
        assert "pagina" in response.json()["data"]
        assert "tamanho" in response.json()["data"]

    def test_ativar_usuario(self, client, headers_admin, usuario_inativo):
        """Teste: Admin pode ativar usuário (RF04)"""
        response = client.patch(
            f"/api/v1/admin/usuarios/{usuario_inativo.id}/ativar",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ATIVO"

    def test_desativar_usuario(self, client, headers_admin, usuario_professor):
        """Teste: Admin pode desativar usuário (RF04)"""
        response = client.patch(
            f"/api/v1/admin/usuarios/{usuario_professor.id}/desativar",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "INATIVO"

    def test_ativar_usuario_sem_admin(self, client, headers_professor, usuario_inativo):
        """Teste: Não-admin não pode ativar usuários"""
        response = client.patch(
            f"/api/v1/admin/usuarios/{usuario_inativo.id}/ativar",
            headers=headers_professor
        )

        assert response.status_code == 403

    def test_ativar_usuario_inexistente(self, client, headers_admin):
        """Teste: Erro ao ativar usuário inexistente"""
        response = client.patch(
            "/api/v1/admin/usuarios/99999/ativar",
            headers=headers_admin
        )

        assert response.status_code == 400

    def test_usuario_inativo_nao_consegue_logar(self, client, usuario_inativo):
        """Teste: Usuário inativo não consegue fazer login (RN01)"""
        dados = {
            "email_ou_usuario": usuario_inativo.email,
            "senha": "senha123456"
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 401
        assert "inativa" in response.json()["detail"].lower()

    def test_usuario_ativado_consegue_logar(self, client, headers_admin, usuario_inativo):
        """Teste: Usuário ativado consegue fazer login"""
        # Ativar usuário
        response_ativar = client.patch(
            f"/api/v1/admin/usuarios/{usuario_inativo.id}/ativar",
            headers=headers_admin
        )
        assert response_ativar.status_code == 200

        # Tentar fazer login
        dados_login = {
            "email_ou_usuario": usuario_inativo.email,
            "senha": "senha123456"
        }
        response_login = client.post("/api/v1/auth/login", json=dados_login)

        assert response_login.status_code == 200
        assert "access_token" in response_login.json()["data"]
