from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== REQUEST DTOs ====================

class MatriculaRequest(BaseModel):
    """DTO para realizar matrícula em curso"""
    curso_id: int = Field(..., description="ID do curso")
    endereco: Optional[str] = Field(None, max_length=500, description="Endereço do aluno")
    genero: Optional[str] = Field(None, max_length=20, description="Gênero do aluno")
    idade: Optional[int] = Field(None, ge=1, le=120, description="Idade do aluno")


class RespostaItemRequest(BaseModel):
    """Uma resposta individual (pergunta + alternativa escolhida)"""
    pergunta_id: int = Field(..., description="ID da pergunta")
    alternativa_id: int = Field(..., description="ID da alternativa escolhida")


# ==================== RESPONSE DTOs ====================

class MatriculaResponse(BaseModel):
    """DTO de resposta de matrícula"""
    id: int
    aluno_id: int
    curso_id: int
    endereco: Optional[str] = None
    genero: Optional[str] = None
    idade: Optional[int] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class ListaMatriculasResponse(BaseModel):
    """DTO de listagem de matrículas"""
    matriculas: List[MatriculaResponse]
    total: int


# ==================== CATÁLOGO ====================

class CursoResumidoResponse(BaseModel):
    """DTO resumido de curso para catálogo"""
    id: int
    titulo: str
    categoria: str
    descricao: str
    carga_horaria: str
    capa: Optional[str] = None
    status: str
    requer_endereco: bool
    requer_genero: bool
    requer_idade: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class ListaCatalogoCursosResponse(BaseModel):
    """DTO de listagem de catálogo de cursos"""
    cursos: List[CursoResumidoResponse]
    total: int


class ModuloResumidoResponse(BaseModel):
    """DTO resumido de módulo para aluno"""
    id: int
    nome: str
    ordem: int
    capa: Optional[str] = None

    class Config:
        from_attributes = True


class ListaModulosResponse(BaseModel):
    """DTO de listagem de módulos"""
    modulos: List[ModuloResumidoResponse]
    total: int


class AulaResumidaResponse(BaseModel):
    """DTO resumido de aula (sem conteúdo) para listagem"""
    id: int
    nome: str
    ordem: int
    tipo_arquivo: Optional[str] = None

    class Config:
        from_attributes = True


class AulaCompletaResponse(BaseModel):
    """DTO completo de aula com conteúdo"""
    id: int
    nome: str
    ordem: int
    arquivo: Optional[str] = None
    tipo_arquivo: Optional[str] = None
    conteudo_ck_editor: Optional[str] = None
    conteudo_gerado: Optional[str] = None

    class Config:
        from_attributes = True


class ListaAulasResponse(BaseModel):
    """DTO de listagem de aulas"""
    aulas: List[AulaResumidaResponse]
    total: int


# ==================== PROVA ====================

class AlternativaSemGabaritoResponse(BaseModel):
    """Alternativa sem indicar se é correta"""
    id: int
    texto: str

    class Config:
        from_attributes = True


class PerguntaSemGabaritoResponse(BaseModel):
    """Pergunta sem gabarito"""
    id: int
    enunciado: str
    ordem: int
    alternativas: List[AlternativaSemGabaritoResponse]

    class Config:
        from_attributes = True


class ProvaSemGabaritoResponse(BaseModel):
    """Prova sem gabarito para aluno"""
    id: int
    modulo_id: int
    perguntas: List[PerguntaSemGabaritoResponse]

    class Config:
        from_attributes = True


class RespostaProvaResponse(BaseModel):
    """Resultado de uma pergunta individual"""
    pergunta_id: int
    enunciado: str
    alternativa_escolhida_id: int
    acertou: Optional[bool] = None
    alternativa_correta_id: Optional[int] = None
    pontos_obtidos: Optional[float] = None
    pontos_possiveis: Optional[float] = None

    class Config:
        from_attributes = True


class ResultadoProvaResponse(BaseModel):
    """Resultado completo da prova"""
    prova_id: int
    pontuacao_obtida: float
    pontuacao_maxima: float
    perguntas: Optional[List[RespostaProvaResponse]] = None

    class Config:
        from_attributes = True
