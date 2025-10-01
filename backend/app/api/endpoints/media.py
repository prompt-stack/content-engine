"""Media API endpoints for image generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from app.services.media.image_generation import ImageGenerationService

router = APIRouter()


class GenerateImageRequest(BaseModel):
    """Request to generate an image"""
    prompt: str
    provider: Literal["openai", "gemini"] = "openai"
    # OpenAI specific
    model: Optional[str] = "dall-e-3"
    size: Optional[str] = "1024x1024"
    quality: Optional[Literal["standard", "hd"]] = "standard"
    style: Optional[Literal["vivid", "natural"]] = "vivid"
    # Gemini specific
    temperature: Optional[float] = 1.0


class GenerateImageResponse(BaseModel):
    """Response from image generation"""
    provider: str
    model: str
    # For OpenAI
    image_url: Optional[str] = None
    revised_prompt: Optional[str] = None
    # For Gemini
    image_data: Optional[str] = None  # base64
    mime_type: Optional[str] = None
    # Common
    size: Optional[str] = None


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    """
    Generate an image using AI.

    **Providers:**
    - **openai**: DALL-E 3 (high quality, paid)
    - **gemini**: Gemini 2.5 Flash Image "nano-banana" (latest, Aug 2025)

    **OpenAI DALL-E 3:**
    - Models: "dall-e-3" (current production model)
    - Note: GPT Image 1 available in limited preview (apply for access)
    - Sizes: "1024x1024", "1792x1024", "1024x1792"
    - Quality: "standard" or "hd"
    - Style: "vivid" (dramatic) or "natural" (realistic)

    **Google Gemini 2.5 Flash Image:**
    - Model: "gemini-2.5-flash-image-preview" (Aug 2025, replaces 2.0)
    - Features: Image blending, character consistency, world knowledge
    - Temperature: 0.0-2.0 (higher = more creative)
    - Pricing: $0.039 per image
    - Returns base64 encoded image data

    **Example Use Cases:**
    - Blog post featured images
    - Social media graphics
    - Content thumbnails
    - Article illustrations
    """
    try:
        service = ImageGenerationService(provider=request.provider)

        if request.provider == "openai":
            result = await service.generate_dalle(
                prompt=request.prompt,
                model=request.model,
                size=request.size,
                quality=request.quality,
                style=request.style
            )
        elif request.provider == "gemini":
            result = service.generate_gemini(
                prompt=request.prompt,
                temperature=request.temperature
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

        return GenerateImageResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.get("/providers")
async def list_providers():
    """
    List available image generation providers and their status.
    """
    from app.core.config import settings

    providers = [
        {
            "name": "openai",
            "display_name": "OpenAI DALL-E & GPT Image",
            "configured": bool(settings.OPENAI_API_KEY),
            "models": {
                "production": ["dall-e-3"],
                "preview": ["gpt-image-1"],  # Limited access
                "legacy": ["dall-e-2"]
            },
            "sizes": {
                "dall-e-3": ["1024x1024", "1792x1024", "1024x1792"],
                "dall-e-2": ["256x256", "512x512", "1024x1024"]
            },
            "features": {
                "dall-e-3": ["High quality", "Style control", "HD option", "Prompt rewriting"],
                "gpt-image-1": ["Superior instruction following", "Text rendering", "Real-world knowledge"]
            },
            "notes": "GPT Image 1 (March 2025) replaces DALL-E in ChatGPT. Apply for API access.",
            "pricing": "Paid per image"
        },
        {
            "name": "gemini",
            "display_name": "Google Gemini & Imagen",
            "configured": bool(settings.GEMINI_API_KEY),
            "models": {
                "gemini_flash": ["gemini-2.5-flash-image-preview"],
                "imagen": ["imagen-4", "imagen-4-ultra"]
            },
            "features": {
                "gemini-2.5-flash": ["Image blending", "Character consistency", "World knowledge", "Multi-turn editing"],
                "imagen-4": ["Superior text rendering", "Precise instruction following"]
            },
            "pricing": {
                "gemini-2.5-flash": "$0.039/image",
                "imagen-4": "$0.04/image"
            },
            "notes": "Gemini 2.5 Flash Image (Aug 2025) replaces 2.0 Flash (deprecated Oct 2025)"
        }
    ]

    return {
        "providers": providers,
        "configured_count": sum(1 for p in providers if p["configured"])
    }


class GenerateFromContentRequest(BaseModel):
    """Request to generate image from content"""
    content: str
    provider: Literal["openai", "gemini"] = "openai"
    prompt_template: Optional[str] = None


@router.post("/generate-from-content")
async def generate_from_content(request: GenerateFromContentRequest):
    """
    Generate an image from extracted content.

    This endpoint takes content (e.g., from a TikTok transcript or article)
    and generates a relevant featured image.

    Args:
        content: The source content (transcript, summary, etc.)
        provider: Image generation provider
        prompt_template: Optional template for prompt generation

    Example:
        content = "AI is transforming how we work..."
        -> Generates: Professional illustration of AI in workplace
    """
    try:
        # Generate a good image prompt from the content
        if request.prompt_template:
            prompt = request.prompt_template.format(content=request.content[:500])
        else:
            # Default: create a featured image style prompt
            content_preview = request.content[:200]
            prompt = f"Create a professional, eye-catching featured image that represents this content: {content_preview}. Style: modern, clean, suitable for social media or blog post."

        service = ImageGenerationService(provider=request.provider)
        result = await service.generate(prompt)

        return {
            "generated_prompt": prompt,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content-based generation failed: {str(e)}")