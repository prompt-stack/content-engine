"""Prompt library service for managing reusable prompts."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class PromptLibrary:
    """Service for loading and managing prompts from config."""

    def __init__(self, prompts_file: str = "config/prompts.json"):
        """Initialize prompt library from JSON file."""
        self.prompts_file = Path(prompts_file)
        self._prompts: Dict = {}
        self._categories: List = []
        self._load_prompts()

    def _load_prompts(self):
        """Load prompts from JSON file."""
        if not self.prompts_file.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_file}")

        with open(self.prompts_file, 'r') as f:
            data = json.load(f)
            self._prompts = data.get('prompts', {})
            self._categories = data.get('categories', [])

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a prompt by ID."""
        return self._prompts.get(prompt_id)

    def list_prompts(self, category: Optional[str] = None) -> List[Dict]:
        """List all prompts, optionally filtered by category."""
        prompts = list(self._prompts.values())

        if category:
            prompts = [p for p in prompts if p.get('category', '').lower() == category.lower()]

        return prompts

    def get_categories(self) -> List[Dict]:
        """Get all prompt categories."""
        return self._categories

    def render_prompt(self, prompt_id: str, variables: Dict[str, str]) -> str:
        """Render a prompt template with variables."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        template = prompt['template']

        # Replace variables in template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            template = template.replace(placeholder, var_value)

        return template

    def validate_prompt(self, prompt_id: str, variables: Dict[str, str]) -> bool:
        """Validate that all required variables are provided."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False

        required_vars = set(prompt.get('variables', []))
        provided_vars = set(variables.keys())

        return required_vars.issubset(provided_vars)


# Singleton instance
_library = None


def get_prompt_library() -> PromptLibrary:
    """Get or create the prompt library instance."""
    global _library
    if _library is None:
        _library = PromptLibrary()
    return _library