"""
Simplified LLM Service for Content Engine
Updated: September 2025

Supports:
- OpenAI: GPT-5, GPT-4.1, GPT-4o, o3/o4-mini (reasoning)
- Anthropic: Claude 4 (Sonnet 4.5, Opus 4.1), Claude 3.7, Claude 3.5
- Google Gemini: 2.5 Pro/Flash/Flash-Lite, 2.0 Flash, 1.5 Pro
- DeepSeek: V3.2-exp (sparse attention), V3.1 (hybrid thinking)
"""

from abc import ABC, abstractmethod
import openai
import anthropic
import google.generativeai as genai
from pydantic import BaseModel
from functools import lru_cache

from app.core.config import settings
from app.models.llm import LLMUsage, LLMResponse


class LLMService(ABC):
    """Abstract base class for LLM services."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using the LLM."""
        pass


class OpenAIService(LLMService):
    """OpenAI implementation of the LLM service."""

    def __init__(self, api_key: str):
        """Initialize the OpenAI client."""
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using OpenAI."""
        # Build messages
        messages = [{"role": "user", "content": prompt}]
        if 'system_prompt' in kwargs:
            messages.insert(0, {"role": "system", "content": kwargs.pop('system_prompt')})

        # Build request parameters
        request_params = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        # Use max_completion_tokens for newer models (GPT-4o+, o-series, GPT-4.1+, GPT-5)
        if model.startswith(("gpt-4o", "o1", "o2", "o3", "o4", "gpt-4.1", "gpt-4.5", "gpt-5")):
            request_params["max_completion_tokens"] = max_tokens
            request_params["temperature"] = temperature
        else:
            request_params["max_tokens"] = max_tokens
            request_params["temperature"] = temperature

        response = await self.client.chat.completions.create(**request_params)

        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )

        return LLMResponse(
            text=response.choices[0].message.content,
            model=model,
            provider="openai",
            usage=usage
        )


class AnthropicService(LLMService):
    """Anthropic (Claude) implementation of the LLM service."""

    def __init__(self, api_key: str):
        """Initialize the Anthropic client."""
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_text(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using Anthropic Claude."""
        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Extract system prompt if provided
        system_prompt = kwargs.pop('system_prompt', None)

        # Build request parameters
        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            **kwargs
        }

        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt

        response = await self.client.messages.create(**request_params)

        usage = LLMUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )

        return LLMResponse(
            text=response.content[0].text,
            model=model,
            provider="anthropic",
            usage=usage
        )


class GeminiService(LLMService):
    """Google Gemini implementation of the LLM service."""

    def __init__(self, api_key: str):
        """Initialize the Gemini client."""
        genai.configure(api_key=api_key)

    async def generate_text(
        self,
        prompt: str,
        model: str = "gemini-1.5-pro",
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using Google Gemini."""
        # Extract system prompt if provided
        system_prompt = kwargs.pop('system_prompt', None)

        # Build the full prompt with system context if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        # Create the model with the specified name
        client = genai.GenerativeModel(model)

        # Generate response
        response = await client.generate_content_async(
            full_prompt,
            generation_config=generation_config
        )

        # Gemini doesn't provide detailed token usage
        estimated_prompt_tokens = len(prompt.split()) * 1.3
        estimated_completion_tokens = len(response.text.split()) * 1.3

        usage = LLMUsage(
            prompt_tokens=int(estimated_prompt_tokens),
            completion_tokens=int(estimated_completion_tokens),
            total_tokens=int(estimated_prompt_tokens + estimated_completion_tokens),
        )

        return LLMResponse(
            text=response.text,
            model=model,
            provider="gemini",
            usage=usage
        )


class DeepSeekService(LLMService):
    """DeepSeek implementation (OpenAI compatible)."""

    def __init__(self, api_key: str):
        """Initialize the DeepSeek client using OpenAI SDK."""
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using DeepSeek."""
        # Build messages
        messages = [{"role": "user", "content": prompt}]
        if 'system_prompt' in kwargs:
            messages.insert(0, {"role": "system", "content": kwargs.pop('system_prompt')})

        # Build request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        response = await self.client.chat.completions.create(**request_params)

        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )

        return LLMResponse(
            text=response.choices[0].message.content,
            model=model,
            provider="deepseek",
            usage=usage
        )


class LLMServiceFactory:
    """Factory for creating LLM service instances."""

    @staticmethod
    def get_service(provider: str) -> LLMService:
        """Get an LLM service by provider name."""
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            return OpenAIService(api_key=settings.OPENAI_API_KEY)
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("Anthropic API key not configured")
            return AnthropicService(api_key=settings.ANTHROPIC_API_KEY)
        elif provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("Gemini API key not configured")
            return GeminiService(api_key=settings.GEMINI_API_KEY)
        elif provider == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DeepSeek API key not configured")
            return DeepSeekService(api_key=settings.DEEPSEEK_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


@lru_cache()
def get_llm_service(provider: str = "openai") -> LLMService:
    """Dependency to get an LLM service."""
    return LLMServiceFactory.get_service(provider)