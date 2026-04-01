class ProvaException(Exception):
    """Exceção base para domínio de prova"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class ProvaNaoEncontradaException(ProvaException):
    """Prova não encontrada"""
    def __init__(self):
        super().__init__("Prova não encontrada", "PROVA_NAO_ENCONTRADA")


class ProvaJaExisteException(ProvaException):
    """Módulo já possui uma prova"""
    def __init__(self):
        super().__init__("Este módulo já possui uma prova", "PROVA_JA_EXISTE")


class PerguntaNaoEncontradaException(ProvaException):
    """Pergunta não encontrada"""
    def __init__(self):
        super().__init__("Pergunta não encontrada", "PERGUNTA_NAO_ENCONTRADA")


class PerguntaInvalidaException(ProvaException):
    """Validação da pergunta falhou"""
    def __init__(self, motivo: str):
        super().__init__(motivo, "PERGUNTA_INVALIDA")
