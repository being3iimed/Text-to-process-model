"""Output file writing utilities."""

import json
from pathlib import Path
from typing import Optional, Dict
from config.settings import (
    OUTPUT_JSON,
    OUTPUT_EXPLANATION,
    OUTPUT_METADATA,
    OUTPUT_RAW_RESPONSE,
)
from utils.text_formatter import format_explanation
from utils.json_parser import make_json_serializable


class OutputWriter:
    """Handles writing various output files."""

    def __init__(self, output_dir: Path):
        """
        Initialize output writer.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def write_json(self, json_obj: dict) -> Optional[Path]:
        """
        Write JSON model to file.

        Args:
            json_obj: JSON object to write

        Returns:
            Path to written file or None
        """
        if not json_obj:
            print("Warning: No JSON object to write")
            return None

        output_file = self.output_dir / OUTPUT_JSON
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=2, ensure_ascii=False)
            print(f"✓ JSON model saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error writing JSON: {e}")
            return None

    def write_raw_json(self, json_str: str) -> Optional[Path]:
        """
        Write raw JSON string when parsing fails.

        Args:
            json_str: Raw JSON string

        Returns:
            Path to written file or None
        """
        if not json_str:
            return None

        output_file = self.output_dir / OUTPUT_JSON
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"✓ Raw JSON saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error writing raw JSON: {e}")
            return None

    def write_explanation(self, text: str) -> Optional[Path]:
        """
        Write formatted explanation to file.

        Args:
            text: Explanation text

        Returns:
            Path to written file or None
        """
        if not text:
            print("Warning: No explanation text to write")
            return None

        output_file = self.output_dir / OUTPUT_EXPLANATION
        try:
            formatted = format_explanation(text)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"✓ Explanation saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error writing explanation: {e}")
            return None

    def write_metadata(self, metadata: Dict) -> Optional[Path]:
        """
        Write metadata to file.

        Args:
            metadata: Metadata dictionary

        Returns:
            Path to written file or None
        """
        if not metadata:
            print("Warning: No metadata to write")
            return None

        output_file = self.output_dir / OUTPUT_METADATA
        try:
            # Make metadata JSON-serializable
            serializable_metadata = {
                key: make_json_serializable(value) for key, value in metadata.items()
            }
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(serializable_metadata, f, indent=2, ensure_ascii=False)
            print(f"✓ Metadata saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error writing metadata: {e}")
            return None

    def write_raw_response(self, content: str) -> Optional[Path]:
        """
        Write full raw response to file.

        Args:
            content: Full response content

        Returns:
            Path to written file or None
        """
        if not content:
            return None

        output_file = self.output_dir / OUTPUT_RAW_RESPONSE
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ Full response saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error writing raw response: {e}")
            return None
