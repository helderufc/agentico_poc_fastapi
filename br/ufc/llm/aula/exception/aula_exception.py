class AulaException(Exception):
    """Exceção base para domínio de aula"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class AulaNaoEncontradaException(AulaException):
    """Aula não encontrada"""
    def __init__(self):
        super().__init__("Aula não encontrada", "AULA_NAO_ENCONTRADA")


class AulaAcessoNegadoException(AulaException):
    """Professor não tem acesso à aula"""
    def __init__(self):
        super().__init__("Você não tem permissão para acessar esta aula", "AULA_ACESSO_NEGADO")
