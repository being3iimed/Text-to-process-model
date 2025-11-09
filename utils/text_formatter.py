"""Text formatting utilities."""

import re
import codecs
from typing import Optional


def decode_escape_sequences(text: str) -> str:
    """
    Decode escape sequences in text.
    
    Args:
        text: Text potentially containing escape sequences
        
    Returns:
        Text with decoded escape sequences
    """
    if '\\n' not in text:
        return text
    
    try:
        return codecs.decode(text, 'unicode_escape')
    except Exception:
        # Fallback: manual replacement
        return text.replace('\\n', '\n')


def format_explanation(text: str) -> str:
    """
    Format explanation text into clean paragraphs.
    
    Args:
        text: Raw explanation text
        
    Returns:
        Formatted explanation
    """
    # Decode escape sequences
    formatted = decode_escape_sequences(text)
    
    # Split into paragraphs
    paragraphs = []
    for para in formatted.split('\n\n'):
        para = para.strip()
        if para:
            # Clean up internal newlines and spaces
            para = re.sub(r'\n+', ' ', para)
            para = re.sub(r' +', ' ', para)
            paragraphs.append(para)
    
    return '\n\n'.join(paragraphs)


def extract_metadata_from_response(response: dict) -> dict:
    """
    Extract metadata from API response.
    
    Args:
        response: API response object
        
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    # Helper function
    def safe_get_attr(obj, attr_name, default=None):
        """Safely get attribute from dict or object."""
        if isinstance(obj, dict):
            return obj.get(attr_name, default)
        elif hasattr(obj, attr_name):
            value = getattr(obj, attr_name, default)
            if hasattr(value, 'dict') and callable(value.dict):
                try:
                    return value.dict()
                except:
                    return value
            return value
        return default
    
    # Extract metadata fields
    response_meta = safe_get_attr(response, 'response_metadata')
    if response_meta:
        metadata["response_metadata"] = response_meta
    
    usage_meta = safe_get_attr(response, 'usage_metadata')
    if usage_meta:
        metadata["usage_metadata"] = usage_meta
    
    msg_id = safe_get_attr(response, 'id')
    if msg_id:
        metadata["id"] = msg_id
    
    kwargs = safe_get_attr(response, 'additional_kwargs')
    if kwargs:
        metadata["additional_kwargs"] = kwargs
    
    return metadata
