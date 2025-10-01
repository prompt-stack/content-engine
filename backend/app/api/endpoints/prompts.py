"""Prompt library API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.prompts.prompt_library import get_prompt_library


router = APIRouter()


class PromptResponse(BaseModel):
    """Response model for a single prompt."""
    id: str
    name: str
    description: str
    category: str
    icon: str
    template: str
    variables: List[str]
    output_format: str
    estimated_tokens: int


class CategoryResponse(BaseModel):
    """Response model for prompt category."""
    id: str
    name: str
    icon: str


class RenderPromptRequest(BaseModel):
    """Request to render a prompt template."""
    prompt_id: str
    variables: Dict[str, str]


@router.get("/list", response_model=List[PromptResponse])
async def list_prompts(category: Optional[str] = None):
    """
    List all available prompts.

    - **category**: Optional category filter (e.g., "Social Media", "Analysis")
    """
    try:
        library = get_prompt_library()
        prompts = library.list_prompts(category=category)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories():
    """List all prompt categories."""
    try:
        library = get_prompt_library()
        categories = library.get_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """
    Get a specific prompt by ID.

    - **prompt_id**: The ID of the prompt (e.g., "summarize", "twitter_thread")
    """
    try:
        library = get_prompt_library()
        prompt = library.get_prompt(prompt_id)

        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")

        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/render")
async def render_prompt(request: RenderPromptRequest):
    """
    Render a prompt template with variables.

    - **prompt_id**: The ID of the prompt template
    - **variables**: Dictionary of variable name/value pairs

    Returns the rendered prompt text ready to send to an LLM.
    """
    try:
        library = get_prompt_library()

        # Validate variables
        if not library.validate_prompt(request.prompt_id, request.variables):
            prompt = library.get_prompt(request.prompt_id)
            required = prompt.get('variables', []) if prompt else []
            raise HTTPException(
                status_code=400,
                detail=f"Missing required variables. Required: {required}, Provided: {list(request.variables.keys())}"
            )

        # Render prompt
        rendered = library.render_prompt(request.prompt_id, request.variables)

        return {
            "prompt_id": request.prompt_id,
            "rendered_prompt": rendered
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render prompt: {str(e)}")