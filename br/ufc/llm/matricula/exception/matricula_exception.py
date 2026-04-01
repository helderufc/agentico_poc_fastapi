class MatriculaException(Exception):
    """Exceção base para matrícula"""
    def __init__(self, message: str = "Erro de matrícula"):
        self.message = message
        super().__init__(message)


class MatriculaJaExisteException(MatriculaException):
    """Aluno já está matriculado neste curso"""
    def __init__(self):
        super().__init__("Aluno já está matriculado neste curso")


class MatriculaNaoEncontradaException(MatriculaException):
    """Matrícula não encontrada"""
    def __init__(self):
        super().__init__("Matrícula não encontrada")


class CursoNaoPublicadoException(MatriculaException):
    """Curso não está publicado"""
    def __init__(self):
        super().__init__("Só é possível se matricular em cursos publicados")


class AcessoNegadoMatriculaException(MatriculaException):
    """Acesso negado — aluno não matriculado"""
    def __init__(self):
        super().__init__("Acesso negado: aluno não está matriculado neste curso")


class PerfilInvalidoException(MatriculaException):
    """Perfil inválido para matrícula"""
    def __init__(self):
        super().__init__("Apenas alunos podem se matricular em cursos")


class DadosMatriculaObrigatoriosException(MatriculaException):
    """Dados obrigatórios não informados"""
    def __init__(self, campo: str):
        super().__init__(f"O campo '{campo}' é obrigatório para este curso")


class RespostaJaExisteException(MatriculaException):
    """Aluno já respondeu esta pergunta"""
    def __init__(self):
        super().__init__("Aluno já respondeu esta pergunta")


class RespostasIncompletasException(MatriculaException):
    """Nem todas as perguntas foram respondidas"""
    def __init__(self):
        super().__init__("Todas as perguntas da prova devem ser respondidas")


class ResultadoNaoEncontradoException(MatriculaException):
    """Aluno ainda não respondeu a prova"""
    def __init__(self):
        super().__init__("Aluno ainda não respondeu esta prova")
