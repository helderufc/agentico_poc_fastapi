from typing import Optional, List
from pydantic import BaseModel, Field


class ModuloEditarRequest(BaseModel):
    """DTO para edição de módulo"""
    nome: Optional[str] = Field(None, max_length=50)


class ModuloResponse(BaseModel):
    """DTO de resposta com dados do módulo"""
    id: int
    nome: str
    ordem: int
    capa: Optional[str] = None
    curso_id: int

    class Config:
        from_attributes = True


class ListaModulosResponse(BaseModel):
    """DTO de resposta para listagem de módulos"""
    modulos: List[ModuloResponse]
    total: int
