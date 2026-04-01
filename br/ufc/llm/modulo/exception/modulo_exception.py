class ModuloException(Exception):
    """Exceção base para domínio de módulo"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class ModuloNaoEncontradoException(ModuloException):
    """Módulo não encontrado"""
    def __init__(self):
        super().__init__("Módulo não encontrado", "MODULO_NAO_ENCONTRADO")


class ModuloAcessoNegadoException(ModuloException):
    """Professor não tem acesso ao módulo"""
    def __init__(self):
        super().__init__("Você não tem permissão para acessar este módulo", "MODULO_ACESSO_NEGADO")
