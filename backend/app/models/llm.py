"""LLM Models"""

from pydantic import BaseModel
from typing import Optional


class LLMUsage(BaseModel):
    """Token usage from LLM request"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMRequest(BaseModel):
    """Request to LLM service"""
    prompt: str
    provider: str = "openai"
    model: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7
    system_prompt: Optional[str] = None


class LLMResponse(BaseModel):
    """Response from LLM service"""
    text: str
    model: str
    provider: str
    usage: LLMUsage