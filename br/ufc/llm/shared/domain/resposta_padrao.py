from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class RespostaPadrao(BaseModel, Generic[T]):
    """
    Modelo padrão de resposta da API.

    Estrutura:
    {
        "data": <dados>,
        "message": "<mensagem>",
        "status": 200
    }
    """
    data: Optional[T] = None
    message: str = ""
    status: int = 200

    class Config:
        json_schema_extra = {
            "example": {
                "data": {},
                "message": "Operação realizada com sucesso",
                "status": 200
            }
        }
