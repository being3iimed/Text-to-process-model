"""File handling utilities."""

from pathlib import Path
from typing import Optional
from config.settings import (
    DEFAULT_INPUT,
    PROMPTS_DIR,
    ERROR_FILE_NOT_FOUND,
    ERROR_PROMPT_NOT_FOUND,
    PROJECT_ROOT,
)


def load_input_content(input_path: Optional[str] = None) -> str:
    """
    Load content from input file.

    Args:
        input_path: Path to input file. If None, uses default.

    Returns:
        Content from input file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if input_path is None:
        input_path = DEFAULT_INPUT
    else:
        input_path = Path(input_path)

    # Try to find file as provided
    if not input_path.exists():
        # Try relative to project root
        root_path = PROJECT_ROOT / input_path
        if root_path.exists():
            input_path = root_path
        else:
            raise FileNotFoundError(ERROR_FILE_NOT_FOUND.format(input_path))

    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def load_prompt(agent_type: str = "modeler") -> str:
    """
    Load prompt for specific agent.

    Args:
        agent_type: Type of agent ("modeler" or "parser")

    Returns:
        Prompt content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    # Try to load .md version first, then .jinja2
    prompt_names = [
        f"{agent_type}_prompt.md",
    ]

    for prompt_name in prompt_names:
        prompt_path = PROMPTS_DIR / prompt_name
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()

    # If nothing found, raise error
    raise FileNotFoundError(
        ERROR_PROMPT_NOT_FOUND.format(f"{agent_type} prompt in {PROMPTS_DIR}")
    )


def ensure_output_dir() -> Path:
    """
    Ensure output directory exists.

    Returns:
        Path to output directory
    """
    from config.settings import OUTPUT_DIR

    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR
