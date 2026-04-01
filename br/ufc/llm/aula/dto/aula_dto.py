from typing import Optional, List
from pydantic import BaseModel, Field


class AulaRequest(BaseModel):
    """DTO para criação/edição de aula"""
    nome: str = Field(..., min_length=1, max_length=255)
    conteudo_ck_editor: Optional[str] = None


class AulaEditarRequest(BaseModel):
    """DTO para edição de aula (campos opcionais)"""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    conteudo_ck_editor: Optional[str] = None


class AulaResponse(BaseModel):
    """DTO de resposta com dados da aula"""
    id: int
    nome: str
    ordem: int
    arquivo: Optional[str] = None
    tipo_arquivo: Optional[str] = None
    conteudo_ck_editor: Optional[str] = None
    conteudo_gerado: Optional[str] = None
    modulo_id: int

    class Config:
        from_attributes = True


class ListaAulasResponse(BaseModel):
    """DTO de resposta para listagem de aulas"""
    aulas: List[AulaResponse]
    total: int


class ConteudoGeradoResponse(BaseModel):
    """Conteúdo HTML gerado pela IA — não persistido ainda (RF26)"""
    conteudo_gerado: str


class ConfirmarConteudoRequest(BaseModel):
    """Payload para persistir o conteúdo gerado (RF28)"""
    conteudo_gerado: str = Field(..., min_length=1)
