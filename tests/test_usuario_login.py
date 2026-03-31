import pytest


class TestLoginUsuario:
    """Testes para login de usuários (RF02)"""

    def test_login_com_sucesso(self, client, usuario_professor):
        """Teste: Login com sucesso"""
        dados = {
            "email_ou_usuario": usuario_professor.email,
            "senha": "senha123456"  # Mesma senha usada na fixture
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 200
        assert "access_token" in response.json()["data"]
        assert "refresh_token" in response.json()["data"]
        assert response.json()["data"]["token_type"] == "bearer"

    def test_login_senha_incorreta(self, client, usuario_professor):
        """Teste: Rejeitar login com senha incorreta"""
        dados = {
            "email_ou_usuario": usuario_professor.email,
            "senha": "senha_errada"
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 401
        assert "inválido" in response.json()["detail"].lower()

    def test_login_usuario_nao_existe(self, client):
        """Teste: Rejeitar login com usuário inexistente"""
        dados = {
            "email_ou_usuario": "naoexiste@example.com",
            "senha": "senha123456"
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 401

    def test_login_usuario_inativo(self, client, usuario_inativo):
        """Teste: Rejeitar login de usuário inativo (RN01)"""
        dados = {
            "email_ou_usuario": usuario_inativo.email,
            "senha": "senha123456"  # Senha correta
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 401
        assert "inativa" in response.json()["detail"].lower()

    def test_login_por_nome(self, client, usuario_professor):
        """Teste: Login usando nome do usuário"""
        dados = {
            "email_ou_usuario": usuario_professor.nome,
            "senha": "senha123456"
        }

        response = client.post("/api/v1/auth/login", json=dados)

        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    def test_refresh_token_valido(self, client, usuario_professor):
        """Teste: Renovar token com refresh token válido"""
        # Primeiro fazer login
        login_dados = {
            "email_ou_usuario": usuario_professor.email,
            "senha": "senha123456"
        }
        login_response = client.post("/api/v1/auth/login", json=login_dados)
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Renovar token
        refresh_dados = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_dados)

        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    def test_refresh_token_inválido(self, client):
        """Teste: Rejeitar refresh token inválido"""
        refresh_dados = {"refresh_token": "token_invalido_123"}
        response = client.post("/api/v1/auth/refresh", json=refresh_dados)

        assert response.status_code == 401
