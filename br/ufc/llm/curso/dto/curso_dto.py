from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CursoRequest(BaseModel):
    """DTO para criação/edição de curso"""
    titulo: str = Field(..., min_length=1, max_length=255)
    categoria: str = Field(..., min_length=1, max_length=100)
    descricao: str = Field(..., min_length=1)
    carga_horaria: str = Field(..., min_length=1, max_length=20)
    requer_endereco: bool = False
    requer_genero: bool = False
    requer_idade: bool = False


class CursoResponse(BaseModel):
    """DTO de resposta com dados do curso"""
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
    professor_id: int
    criado_em: datetime

    class Config:
        from_attributes = True


class ListaCursosResponse(BaseModel):
    """DTO de resposta para listagem de cursos"""
    cursos: List[CursoResponse]
    total: int
