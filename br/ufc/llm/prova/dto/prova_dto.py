from typing import Optional, List
from pydantic import BaseModel, Field


class AlternativaRequest(BaseModel):
    """DTO para criação de alternativa"""
    texto: str = Field(..., min_length=1, max_length=1000)
    correta: bool = False


class AlternativaResponse(BaseModel):
    """DTO de resposta de alternativa"""
    id: int
    texto: str
    correta: bool
    pergunta_id: int

    class Config:
        from_attributes = True


class PerguntaRequest(BaseModel):
    """DTO para criação/edição de pergunta"""
    enunciado: str = Field(..., min_length=1, max_length=2000)
    pontos: int = Field(default=1, ge=1)
    alternativas: List[AlternativaRequest] = Field(..., min_length=2)


class PerguntaResponse(BaseModel):
    """DTO de resposta de pergunta"""
    id: int
    enunciado: str
    pontos: int
    ordem: int
    prova_id: int
    alternativas: List[AlternativaResponse] = []

    class Config:
        from_attributes = True


class ProvaRequest(BaseModel):
    """DTO para criação/edição de prova"""
    mostrar_respostas_erradas: bool = False
    mostrar_respostas_corretas: bool = False
    mostrar_valores: bool = False


class ProvaResponse(BaseModel):
    """DTO de resposta de prova"""
    id: int
    modulo_id: int
    mostrar_respostas_erradas: bool
    mostrar_respostas_corretas: bool
    mostrar_valores: bool
    perguntas: List[PerguntaResponse] = []

    class Config:
        from_attributes = True


# ==================== ESTATÍSTICAS (RF34) ====================

class AlternativaEstatisticaResponse(BaseModel):
    """Contagem de respostas por alternativa"""
    alternativa_id: int
    texto: str
    total_respostas: int
    percentual: float


class PerguntaEstatisticaResponse(BaseModel):
    """Estatísticas de uma pergunta"""
    pergunta_id: int
    enunciado: str
    total_respostas: int
    alternativas: List[AlternativaEstatisticaResponse]


class EstatisticasProvaResponse(BaseModel):
    """Estatísticas completas da prova (RF34)"""
    prova_id: int
    total_respondentes: int
    perguntas: List[PerguntaEstatisticaResponse]


# ==================== QUIZ IA (RF35) ====================

class AlternativaQuizResponse(BaseModel):
    texto: str
    correta: bool


class PerguntaQuizResponse(BaseModel):
    enunciado: str
    pontos: int
    alternativas: List[AlternativaQuizResponse]


class QuizGeradoResponse(BaseModel):
    """Sugestão de quiz gerada pela IA — não persistida (RF35-RF36)"""
    perguntas: List[PerguntaQuizResponse]
