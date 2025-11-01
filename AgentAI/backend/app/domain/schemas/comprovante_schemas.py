"""Comprovante Response Schemas"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ComprovanteResponse(BaseModel):
    """Response do upload de comprovante"""
    success: bool = Field(
        ...,
        description="Indica se o upload foi bem-sucedido"
    )
    message: str = Field(
        ...,
        description="Mensagem de retorno"
    )
    cpf: Optional[str] = Field(
        default=None,
        description="CPF extraído do comprovante"
    )
    valor: Optional[float] = Field(
        default=None,
        description="Valor extraído do comprovante"
    )
    data: Optional[str] = Field(
        default=None,
        description="Data extraída do comprovante"
    )
    filename: Optional[str] = Field(
        default=None,
        description="Nome do arquivo salvo"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalhes adicionais da validação"
    )
