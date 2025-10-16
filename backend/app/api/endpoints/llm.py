"""LLM API endpoints for content processing."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.limiter import limiter
from app.services.llm.llm_service import get_llm_service
from app.models.llm import LLMRequest, LLMResponse as LLMResponseModel
from app.api.deps import verify_api_key

router = APIRouter()


class ProcessContentRequest(BaseModel):
    """Request to process extracted content with LLM"""
    content: str
    task: str  # e.g. "summarize", "extract_key_points", "analyze_sentiment"
    provider: str = "openai"
    model: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7


class ProcessContentResponse(BaseModel):
    """Response from content processing"""
    result: str
    task: str
    model: str
    provider: str
    usage: dict


@router.post("/generate", response_model=LLMResponseModel)
@limiter.limit("10/minute")
async def generate_text(
    llm_request: LLMRequest,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    Generate text using specified LLM provider.

    **Rate Limit:** 10 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **prompt**: Text prompt to send to LLM
    - **provider**: LLM provider (openai, anthropic, gemini, deepseek)
    - **model**: Specific model to use (optional, uses default)
    - **max_tokens**: Maximum tokens in response
    - **temperature**: Sampling temperature (0-1)
    """
    from app.core.config import settings
    if not settings.ENABLE_LLM:
        raise HTTPException(
            status_code=503,
            detail="LLM features are currently disabled for cost control. Please contact administrator."
        )

    try:
        service = get_llm_service(llm_request.provider)

        # Build kwargs
        kwargs = {}
        if llm_request.system_prompt:
            kwargs['system_prompt'] = llm_request.system_prompt

        response = await service.generate_text(
            prompt=llm_request.prompt,
            model=llm_request.model or get_default_model(llm_request.provider),
            max_tokens=llm_request.max_tokens,
            temperature=llm_request.temperature,
            **kwargs
        )

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")


@router.post("/process-content", response_model=ProcessContentResponse)
@limiter.limit("10/minute")
async def process_content(
    content_request: ProcessContentRequest,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    Process extracted content with AI.

    **Rate Limit:** 10 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    Common tasks:
    - **summarize**: Create a concise summary
    - **extract_key_points**: Extract main points as bullet list
    - **analyze_sentiment**: Determine sentiment (positive/negative/neutral)
    - **generate_tags**: Generate relevant tags/keywords
    - **translate**: Translate to another language (specify in task)
    """
    from app.core.config import settings
    if not settings.ENABLE_LLM:
        raise HTTPException(
            status_code=503,
            detail="LLM features are currently disabled for cost control. Please contact administrator."
        )

    try:
        service = get_llm_service(content_request.provider)

        # Build prompt based on task
        prompt = build_task_prompt(content_request.task, content_request.content)

        response = await service.generate_text(
            prompt=prompt,
            model=content_request.model or get_default_model(content_request.provider),
            max_tokens=content_request.max_tokens,
            temperature=content_request.temperature
        )

        return ProcessContentResponse(
            result=response.text,
            task=content_request.task,
            model=response.model,
            provider=response.provider,
            usage=response.usage.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content processing failed: {str(e)}")


@router.get("/providers")
async def list_providers():
    """
    List available LLM providers and their configuration status.
    """
    from app.core.config import settings

    providers = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "configured": bool(settings.OPENAI_API_KEY),
            "default_model": "gpt-4o-mini",
            "models": {
                "gpt5": ["gpt-5"],  # Latest flagship (Aug 2025)
                "gpt4_series": ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini"],  # GPT-4.1 (latest API), 4o
                "o_series": ["o3", "o3-pro", "o4-mini", "o1", "o1-mini"],  # Reasoning models
                "legacy": ["gpt-4.5"]  # Research preview (deprecated in 3 months)
            },
            "notes": {
                "gpt-5": "Default in ChatGPT (Aug 2025)",
                "gpt-4.1": "Latest API model, 1M context, beats 4o",
                "o3": "Most powerful reasoning, 20% fewer errors than o1",
                "o4-mini": "Cost-efficient reasoning"
            },
            "context": "Up to 1M tokens",
            "features": ["Web search", "File analysis", "Vision", "Image generation (via tools)"]
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic Claude",
            "configured": bool(settings.ANTHROPIC_API_KEY),
            "default_model": "claude-sonnet-4.5",
            "models": {
                "claude4": ["claude-sonnet-4.5", "claude-sonnet-4", "claude-opus-4.1", "claude-opus-4"],  # Claude 4 family (May 2025)
                "claude3_7": ["claude-3-7-sonnet"],  # Hybrid reasoning (Feb 2025)
                "claude3_5": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]  # Legacy
            },
            "notes": {
                "claude-sonnet-4.5": "Best model for complex agents/coding (highest intelligence)",
                "claude-opus-4.1": "Best coding model (72.5% SWE-bench, 43.2% Terminal-bench)",
                "claude-3-7-sonnet": "First hybrid reasoning model (choose thinking depth)",
                "claude-sonnet-4": "72.7% SWE-bench, state-of-the-art coding"
            },
            "context": "1M tokens (with beta header)",
            "features": ["128k output tokens (with beta)", "Hybrid reasoning", "Extended thinking"]
        },
        {
            "name": "gemini",
            "display_name": "Google Gemini",
            "configured": bool(settings.GEMINI_API_KEY),
            "default_model": "gemini-2.5-pro",
            "models": {
                "gemini2_5": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],  # Sept 2025 stable
                "gemini2_0": ["gemini-2.0-flash"],  # 2.0 generation
                "gemini1_5": ["gemini-1.5-pro", "gemini-pro"]  # Legacy
            },
            "notes": {
                "gemini-2.5-pro": "Flagship with adaptive thinking (63.8% SWE-Bench)",
                "gemini-2.5-flash": "Fast with thinking capabilities",
                "gemini-2.5-flash-lite": "Lowest latency/cost, high throughput",
                "gemini-2.0-flash": "Native tool use, 1M context"
            },
            "context": "1M tokens (2M coming soon)",
            "features": ["Adaptive thinking", "Math/science benchmarks leader", "Native image generation"]
        },
        {
            "name": "deepseek",
            "display_name": "DeepSeek",
            "configured": bool(settings.DEEPSEEK_API_KEY),
            "default_model": "deepseek-chat",
            "models": {
                "v3_2": ["deepseek-v3.2-exp"],  # Sept 2025 - Sparse attention
                "v3_1": ["deepseek-chat", "deepseek-reasoner"],  # Aug 2025 - Hybrid (v3.1-Terminus)
            },
            "notes": {
                "deepseek-v3.2-exp": "Sparse attention, 50% cost reduction ($0.028/M input tokens)",
                "deepseek-chat": "V3.1 non-thinking mode (direct answers)",
                "deepseek-reasoner": "V3.1 thinking mode (chain-of-thought reasoning)",
                "v3.1": "671B params (37B activated), 128K context, hybrid thinking"
            },
            "context": "128K tokens",
            "pricing": "Most cost-effective: $0.028/M input (v3.2)",
            "features": ["Sparse attention", "Hybrid thinking modes", "Smarter tool calling", "OpenAI API compatible"]
        }
    ]

    return {
        "providers": providers,
        "configured_count": sum(1 for p in providers if p["configured"])
    }


def get_default_model(provider: str) -> str:
    """Get default model for provider (Updated Sept 2025)"""
    defaults = {
        "openai": "gpt-4o-mini",  # Most cost-effective for general use
        "anthropic": "claude-3-5-sonnet-20241022",  # Using legacy until 4.5 widely available
        "gemini": "gemini-2.5-flash",  # Fast with thinking capabilities
        "deepseek": "deepseek-chat"  # V3.1 non-thinking mode
    }
    return defaults.get(provider, "gpt-4o-mini")


def build_task_prompt(task: str, content: str) -> str:
    """Build prompt based on task type"""
    task_prompts = {
        "summarize": f"Provide a concise summary of the following content:\n\n{content}",
        "extract_key_points": f"Extract the key points from the following content as a bullet list:\n\n{content}",
        "analyze_sentiment": f"Analyze the sentiment of the following content (positive, negative, or neutral) and explain why:\n\n{content}",
        "generate_tags": f"Generate 5-10 relevant tags/keywords for the following content:\n\n{content}",
        "extract_entities": f"Extract named entities (people, organizations, locations) from the following content:\n\n{content}",
    }

    return task_prompts.get(task, f"Task: {task}\n\nContent:\n{content}")