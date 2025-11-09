"""JSON extraction and parsing utilities."""

import json
import re
import codecs
from typing import Tuple, Optional


def extract_json_from_text(content: str) -> Tuple[Optional[str], str]:
    """
    Extract JSON from markdown code blocks or by matching braces.

    Args:
        content: Text containing JSON

    Returns:
        Tuple of (json_string, explanation_text)
    """
    json_str = None
    explanation_text = content

    # Method 1: Try markdown code blocks
    json_str, explanation_text = _extract_from_code_fence(content)

    # Method 2: Try matching braces if no code fence found
    if not json_str:
        json_str, explanation_text = _extract_from_braces(content)

    return json_str, explanation_text


def _extract_from_code_fence(content: str) -> Tuple[Optional[str], str]:
    """Extract JSON from markdown code fence (```json ... ```)."""
    code_fence_pattern = r"```(?:json)?\s*\n"
    fence_start = re.search(code_fence_pattern, content, re.IGNORECASE)

    if fence_start:
        start_pos = fence_start.end()
        fence_end = content.find("```", start_pos)

        if fence_end != -1:
            json_str = content[start_pos:fence_end].strip()
            # Remove code block from explanation
            full_block_start = fence_start.start()
            full_block_end = fence_end + 3
            explanation = (
                content[:full_block_start] + content[full_block_end:]
            ).strip()
            return json_str, explanation

    return None, content


def _extract_from_braces(content: str) -> Tuple[Optional[str], str]:
    """Extract JSON by matching braces."""
    brace_start = content.find("{")

    if brace_start != -1:
        brace_count = 0
        brace_end = brace_start

        for i in range(brace_start, len(content)):
            if content[i] == "{":
                brace_count += 1
            elif content[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    brace_end = i + 1
                    break

        if brace_count == 0:
            json_str = content[brace_start:brace_end]
            explanation = (content[:brace_start] + content[brace_end:]).strip()
            return json_str, explanation

    return None, content


def parse_json(json_str: str) -> Optional[dict]:
    """
    Parse JSON string with multiple fallback strategies.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed JSON object or None
    """
    # Strategy 1: Direct parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Decode unicode escape sequences
    try:
        decoded_str = json_str.encode("latin-1").decode("unicode_escape")
        return json.loads(decoded_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    # Strategy 3: Use codecs
    try:
        decoded_str = codecs.decode(json_str, "unicode_escape")
        return json.loads(decoded_str)
    except Exception:
        pass

    # All strategies failed
    return None


def make_json_serializable(obj: any) -> any:
    """
    Convert object to JSON-serializable format.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of object
    """
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)
