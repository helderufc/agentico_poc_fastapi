import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import Base, get_db
from br.ufc.llm.usuario.domain.usuario import Usuario, TokenRecuperacaoSenha
from br.ufc.llm.shared.domain.seguranca import SenhaUtil

# Configurar banco de testes em memória
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    """Criar banco de testes e retornar sessão"""
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """Criar cliente FastAPI com dependência de banco de testes"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_professor(db_session):
    """Criar usuário PROFESSOR para testes"""
    usuario = Usuario(
        nome="Prof. João Silva",
        cpf="12345678901",
        email="professor@example.com",
        senha=SenhaUtil.hash_senha("senha123456"),
        perfil="PROFESSOR",
        status="ATIVO"
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def usuario_aluno(db_session):
    """Criar usuário ALUNO para testes"""
    usuario = Usuario(
        nome="João Aluno",
        cpf="98765432101",
        email="aluno@example.com",
        senha=SenhaUtil.hash_senha("senha123456"),
        perfil="ALUNO",
        status="ATIVO"
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def usuario_admin(db_session):
    """Criar usuário ADMIN para testes"""
    usuario = Usuario(
        nome="Admin User",
        cpf="11122233344",
        email="admin@example.com",
        senha=SenhaUtil.hash_senha("admin123456"),
        perfil="ADMIN",
        status="ATIVO"
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def usuario_inativo(db_session):
    """Criar usuário INATIVO para testes"""
    usuario = Usuario(
        nome="Inativo User",
        cpf="55566677788",
        email="inativo@example.com",
        senha=SenhaUtil.hash_senha("senha123456"),
        perfil="PROFESSOR",
        status="INATIVO"
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def token_professor(client, usuario_professor):
    """Gerar token JWT para usuário professor"""
    from br.ufc.llm.shared.domain.seguranca import JWTUtil
    tokens = JWTUtil.gerar_tokens(
        usuario_id=usuario_professor.id,
        email=usuario_professor.email,
        perfil=usuario_professor.perfil
    )
    return tokens["access_token"]


@pytest.fixture
def token_admin(client, usuario_admin):
    """Gerar token JWT para usuário admin"""
    from br.ufc.llm.shared.domain.seguranca import JWTUtil
    tokens = JWTUtil.gerar_tokens(
        usuario_id=usuario_admin.id,
        email=usuario_admin.email,
        perfil=usuario_admin.perfil
    )
    return tokens["access_token"]


@pytest.fixture
def headers_professor(token_professor):
    """Headers com token de professor"""
    return {"Authorization": f"Bearer {token_professor}"}


@pytest.fixture
def headers_admin(token_admin):
    """Headers com token de admin"""
    return {"Authorization": f"Bearer {token_admin}"}
