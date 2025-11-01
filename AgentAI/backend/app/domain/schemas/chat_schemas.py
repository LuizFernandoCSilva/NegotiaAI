"""Chat Request/Response Schemas"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configurações do LLM"""
    model: Optional[str] = Field(
        default="gemini-2.0-flash-exp",
        description="Modelo do LLM",
        examples=["gemini-2.0-flash-exp"]
    )
    temperature: Optional[float] = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperatura do modelo (0.0 a 2.0)"
    )
    max_tokens: Optional[int] = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Máximo de tokens na resposta"
    )


class ChatRequest(BaseModel):
    """Request para enviar mensagem ao agente"""
    message: str = Field(
        ...,
        description="Mensagem do usuário",
        min_length=1,
        examples=["Olá, gostaria de negociar minha dívida"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID da sessão (gerado automaticamente se omitido)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    user_id: Optional[str] = Field(
        default=None,
        description="ID do usuário",
        examples=["user_20251026_140000"]
    )
    llm_config: Optional[LLMConfig] = Field(
        default=None,
        description="Configurações avançadas do LLM (opcional)"
    )


class ChatResponse(BaseModel):
    """Response do agente"""
    response: str = Field(
        ...,
        description="Resposta do agente"
    )
    session_id: str = Field(
        ...,
        description="ID da sessão"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais da conversa"
    )


class EndSessionRequest(BaseModel):
    """Request para encerrar sessão"""
    session_id: str = Field(
        ...,
        description="ID da sessão a ser encerrada",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
