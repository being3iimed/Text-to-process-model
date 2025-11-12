"""Configuration settings for BPMN Modeler."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# API Configuration
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
MISTRAL_MODEL = "magistral-medium-latest"
MISTRAL_TEMPERATURE = 0.2
MISTRAL_MAX_RETRIES = 3

# File Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Default files
DEFAULT_PROMPT = PROMPTS_DIR / "modeler_prompt.md"
DEFAULT_INPUT = INPUT_DIR / "parser_output.txt"

# Output files
OUTPUT_JSON = "bpmn_model.json"
OUTPUT_EXPLANATION = "explanation.txt"
OUTPUT_METADATA = "metadata.json"
OUTPUT_RAW_RESPONSE = "full_response.txt"

# Error messages
ERROR_API_KEY_MISSING = (
    "MISTRAL_API_KEY not provided (set env or run interactively to enter it)"
)
ERROR_FILE_NOT_FOUND = "Input file not found: {}"
ERROR_PROMPT_NOT_FOUND = "Prompt file not found: {}"

# LangSmith Configuration
LANGSMITH_ENABLED = os.getenv("LANGSMITH_TRACING_V2", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "text-to-process-model")

# API Error Messages
ERROR_RATE_LIMIT = "ERROR: Mistral API Rate Limit Exceeded (429)"
ERROR_RATE_LIMIT_MSG = """
Service tier capacity exceeded for this model.

Possible solutions:
1. Wait a few minutes and try again
2. Upgrade your Mistral API tier/plan
3. Try using a different model (e.g., 'mistral-medium-latest')
4. Check your API usage limits at https://console.mistral.ai/
"""
