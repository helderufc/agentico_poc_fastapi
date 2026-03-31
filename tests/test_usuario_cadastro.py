import pytest


class TestCadastroUsuario:
    """Testes para cadastro de usuários (RF01)"""

    def test_cadastro_com_sucesso(self, client):
        """Teste: Cadastrar novo usuário com sucesso"""
        dados = {
            "nome": "Novo Usuario",
            "cpf": "12345678901",
            "email": "novo@example.com",
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 201
        assert response.json()["status"] == 201
        assert response.json()["data"]["email"] == "novo@example.com"
        assert response.json()["data"]["status"] == "INATIVO"  # RN01

    def test_cadastro_cpf_duplicado(self, client, usuario_professor):
        """Teste: Não permitir CPF duplicado"""
        dados = {
            "nome": "Outro Usuario",
            "cpf": usuario_professor.cpf,  # Mesmo CPF
            "email": "outro@example.com",
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 400
        assert "já existe" in response.json()["detail"].lower()

    def test_cadastro_email_duplicado(self, client, usuario_professor):
        """Teste: Não permitir e-mail duplicado"""
        dados = {
            "nome": "Outro Usuario",
            "cpf": "98765432101",
            "email": usuario_professor.email,  # Mesmo e-mail
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 400
        assert "já existe" in response.json()["detail"].lower()

    def test_cadastro_cpf_invalido(self, client):
        """Teste: Rejeitar CPF com formato inválido"""
        dados = {
            "nome": "Usuario Invalido",
            "cpf": "123",  # Menos de 11 dígitos
            "email": "invalido@example.com",
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 422  # Validação Pydantic

    def test_cadastro_senha_curta(self, client):
        """Teste: Rejeitar senha com menos de 8 caracteres"""
        dados = {
            "nome": "Usuario Invalido",
            "cpf": "12345678901",
            "email": "invalido@example.com",
            "senha": "123",  # Muito curta
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 422

    def test_cadastro_email_invalido(self, client):
        """Teste: Rejeitar e-mail inválido"""
        dados = {
            "nome": "Usuario Invalido",
            "cpf": "12345678901",
            "email": "nao-eh-email",  # Email inválido
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 422

    def test_cadastro_nome_muito_curto(self, client):
        """Teste: Rejeitar nome com menos de 3 caracteres"""
        dados = {
            "nome": "Jo",  # Muito curto
            "cpf": "12345678901",
            "email": "jo@example.com",
            "senha": "senha123456",
            "perfil": "PROFESSOR"
        }

        response = client.post("/api/v1/auth/cadastro", json=dados)

        assert response.status_code == 422
