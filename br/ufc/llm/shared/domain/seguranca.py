import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import bcrypt
from config import settings
from br.ufc.llm.usuario.exception.usuario_exception import JWTInvalidoException


class SenhaUtil:
    """Utilidades para hash e validação de senhas com bcrypt"""

    @staticmethod
    def hash_senha(senha: str) -> str:
        """Hash de senha com bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def validar_senha(senha_plana: str, senha_hash: str) -> bool:
        """Validar senha em relação ao hash"""
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))


class JWTUtil:
    """Utilidades para geração e validação de JWT"""

    ALGORITMO = settings.ALGORITHM
    CHAVE_SECRETA = settings.SECRET_KEY

    @staticmethod
    def gerar_tokens(
        usuario_id: int,
        email: str,
        perfil: str,
        access_expires_minutes: Optional[int] = None,
        refresh_expires_days: int = 7
    ) -> Dict[str, Any]:
        """
        Gerar par de tokens (access + refresh)

        Args:
            usuario_id: ID do usuário
            email: E-mail do usuário
            perfil: Perfil do usuário
            access_expires_minutes: Minutos até expiração do access token
            refresh_expires_days: Dias até expiração do refresh token

        Returns:
            Dict com access_token, refresh_token, tipo, e expires_in
        """
        if access_expires_minutes is None:
            access_expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        agora = datetime.now(timezone.utc)

        # Access token - curta duração
        access_expires = agora + timedelta(minutes=access_expires_minutes)
        access_payload = {
            "sub": usuario_id,
            "email": email,
            "perfil": perfil,
            "exp": access_expires,
            "type": "access",
            "iat": agora
        }
        access_token = jwt.encode(access_payload, JWTUtil.CHAVE_SECRETA, algorithm=JWTUtil.ALGORITMO)

        # Refresh token - longa duração
        refresh_expires = agora + timedelta(days=refresh_expires_days)
        refresh_payload = {
            "sub": usuario_id,
            "email": email,
            "exp": refresh_expires,
            "type": "refresh",
            "iat": agora
        }
        refresh_token = jwt.encode(refresh_payload, JWTUtil.CHAVE_SECRETA, algorithm=JWTUtil.ALGORITMO)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_expires_minutes * 60  # em segundos
        }

    @staticmethod
    def validar_token(token: str, tipo_esperado: str = "access") -> Dict[str, Any]:
        """
        Validar e decodificar JWT

        Args:
            token: Token JWT a validar
            tipo_esperado: Tipo esperado (access ou refresh)

        Returns:
            Payload decodificado

        Raises:
            JWTInvalidoException: Se token for inválido ou expirado
        """
        try:
            payload = jwt.decode(token, JWTUtil.CHAVE_SECRETA, algorithms=[JWTUtil.ALGORITMO])

            # Validar tipo de token se especificado
            if tipo_esperado and payload.get("type") != tipo_esperado:
                raise JWTInvalidoException()

            return payload
        except jwt.ExpiredSignatureError:
            raise JWTInvalidoException()
        except jwt.InvalidTokenError:
            raise JWTInvalidoException()

    @staticmethod
    def extrair_usuario_id_do_token(token: str) -> int:
        """Extrair ID do usuário do token"""
        payload = JWTUtil.validar_token(token)
        return payload.get("sub")


class TokenRecuperacaoUtil:
    """Utilidades para geração de tokens de recuperação de senha"""

    TAMANHO_TOKEN = 32  # 32 bytes = 256 bits
    EXPIRACAO_MINUTOS = 30

    @staticmethod
    def gerar_token() -> str:
        """Gerar token aleatório seguro para recuperação de senha"""
        return secrets.token_urlsafe(TokenRecuperacaoUtil.TAMANHO_TOKEN)

    @staticmethod
    def calcular_expiracao() -> datetime:
        """Calcular data/hora de expiração (30 min a partir de agora)"""
        return datetime.utcnow() + timedelta(minutes=TokenRecuperacaoUtil.EXPIRACAO_MINUTOS)

    @staticmethod
    def token_expirado(data_expiracao: datetime) -> bool:
        """Verificar se token está expirado"""
        return datetime.utcnow() > data_expiracao
