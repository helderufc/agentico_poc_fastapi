class CursoException(Exception):
    """Exceção base para domínio de curso"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class CursoNaoEncontradoException(CursoException):
    """Curso não encontrado"""
    def __init__(self):
        super().__init__("Curso não encontrado", "CURSO_NAO_ENCONTRADO")


class CursoAcessoNegadoException(CursoException):
    """Professor não é dono do curso"""
    def __init__(self):
        super().__init__("Você não tem permissão para acessar este curso", "CURSO_ACESSO_NEGADO")
