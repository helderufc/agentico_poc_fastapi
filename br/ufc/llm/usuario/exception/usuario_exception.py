class UsuarioException(Exception):
    """Exceção base para domínio de usuário"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class UsuarioJaExisteException(UsuarioException):
    """Usuário já existe (CPF ou e-mail duplicado)"""
    def __init__(self, campo: str):
        super().__init__(f"Usuário com este {campo} já existe no sistema", "USUARIO_JA_EXISTE")


class UsuarioNaoEncontradoException(UsuarioException):
    """Usuário não encontrado"""
    def __init__(self, campo: str = "id"):
        super().__init__(f"Usuário não encontrado com o {campo} informado", "USUARIO_NAO_ENCONTRADO")


class CredenciaisInvalidasException(UsuarioException):
    """Credenciais de login inválidas"""
    def __init__(self):
        super().__init__("E-mail/nome de usuário ou senha inválidos", "CREDENCIAIS_INVALIDAS")


class UsuarioInativoException(UsuarioException):
    """Usuário está inativo e não pode fazer login"""
    def __init__(self):
        super().__init__("Sua conta está inativa. Aguarde ativação por um administrador", "USUARIO_INATIVO")


class TokenExpiradoException(UsuarioException):
    """Token de recuperação expirou ou já foi usado"""
    def __init__(self):
        super().__init__("Token expirado ou inválido. Solicite uma nova recuperação", "TOKEN_EXPIRADO")


class SenhaInvalidaException(UsuarioException):
    """Senha atual está incorreta"""
    def __init__(self):
        super().__init__("Senha atual está incorreta", "SENHA_INVALIDA")


class JWTInvalidoException(UsuarioException):
    """Token JWT inválido ou expirado"""
    def __init__(self):
        super().__init__("Token de autenticação inválido ou expirado", "JWT_INVALIDO")


class AcessoNegadoException(UsuarioException):
    """Usuário não tem permissão para acessar o recurso"""
    def __init__(self, recurso: str = "recurso"):
        super().__init__(f"Você não tem permissão para acessar este {recurso}", "ACESSO_NEGADO")
