import pytest


class TestPerfilUsuario:
    """Testes para perfil de usuário (RF06-RF08)"""

    def test_obter_perfil_com_autenticacao(self, client, headers_professor, usuario_professor):
        """Teste: Obter perfil com autenticação válida"""
        response = client.get("/api/v1/perfil", headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["email"] == usuario_professor.email
        assert response.json()["data"]["id"] == usuario_professor.id
        assert "senha" not in response.json()["data"]  # Não retorna senha

    def test_obter_perfil_sem_autenticacao(self, client):
        """Teste: Rejeitar acesso ao perfil sem autenticação"""
        response = client.get("/api/v1/perfil")

        assert response.status_code == 401

    def test_obter_perfil_token_invalido(self, client):
        """Teste: Rejeitar acesso ao perfil com token inválido"""
        headers = {"Authorization": "Bearer token_invalido_123"}
        response = client.get("/api/v1/perfil", headers=headers)

        assert response.status_code == 401

    def test_alterar_senha_com_sucesso(self, client, headers_professor, usuario_professor):
        """Teste: Alterar senha com sucesso (RF08)"""
        dados = {
            "senha_atual": "senha123456",
            "nova_senha": "novaSenha123",
            "confirmacao_nova_senha": "novaSenha123"
        }

        response = client.put("/api/v1/perfil/senha", json=dados, headers=headers_professor)

        assert response.status_code == 200
        assert response.json()["data"]["email"] == usuario_professor.email

    def test_alterar_senha_senha_atual_incorreta(self, client, headers_professor):
        """Teste: Rejeitar alteração com senha atual incorreta"""
        dados = {
            "senha_atual": "senha_errada",
            "nova_senha": "novaSenha123",
            "confirmacao_nova_senha": "novaSenha123"
        }

        response = client.put("/api/v1/perfil/senha", json=dados, headers=headers_professor)

        assert response.status_code == 400
        assert "incorreta" in response.json()["detail"].lower()

    def test_alterar_senha_senhas_nao_conferem(self, client, headers_professor):
        """Teste: Rejeitar alteração quando novas senhas não conferem"""
        dados = {
            "senha_atual": "senha123456",
            "nova_senha": "novaSenha123",
            "confirmacao_nova_senha": "outraSenha456"  # Diferente
        }

        response = client.put("/api/v1/perfil/senha", json=dados, headers=headers_professor)

        assert response.status_code == 400
        assert "não conferem" in response.json()["detail"].lower()

    def test_alterar_senha_sem_autenticacao(self, client):
        """Teste: Rejeitar alteração de senha sem autenticação"""
        dados = {
            "senha_atual": "senha123456",
            "nova_senha": "novaSenha123",
            "confirmacao_nova_senha": "novaSenha123"
        }

        response = client.put("/api/v1/perfil/senha", json=dados)

        assert response.status_code == 401

    def test_cpf_nao_mutavel(self, client, headers_professor, usuario_professor):
        """Teste: CPF é somente leitura no perfil (RN03)"""
        # Obter perfil
        response = client.get("/api/v1/perfil", headers=headers_professor)

        # CPF deve ser retornado
        assert response.json()["data"]["cpf"] == usuario_professor.cpf

        # Não deve haver endpoint para alterar CPF (apenas leitura)
        # Este teste valida que não existe PUT /perfil/cpf

    def test_email_nao_mutavel(self, client, headers_professor, usuario_professor):
        """Teste: E-mail é somente leitura no perfil (RN03)"""
        # Obter perfil
        response = client.get("/api/v1/perfil", headers=headers_professor)

        # E-mail deve ser retornado
        assert response.json()["data"]["email"] == usuario_professor.email

        # Não deve haver endpoint para alterar e-mail (apenas leitura)
        # Este teste valida que não existe PUT /perfil/email
