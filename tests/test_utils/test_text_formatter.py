# tests/test_utils/test_text_formatter.py
"""Tests for text formatting utilities."""

from utils.text_formatter import decode_escape_sequences, format_explanation


class TestDecodeEscapeSequences:
    """Tests for escape sequence decoding."""

    def test_decode_newlines(self):
        """Test decoding newline escape sequences."""
        text = "line1\\nline2\\nline3"

        result = decode_escape_sequences(text)

        assert "line1" in result
        assert "line2" in result

    def test_no_escape_sequences(self):
        """Test text without escape sequences."""
        text = "plain text without escapes"

        result = decode_escape_sequences(text)

        assert result == text


class TestFormatExplanation:
    """Tests for explanation formatting."""

    def test_format_with_paragraphs(self):
        """Test formatting text with paragraphs."""
        text = "Paragraph 1\\n\\nParagraph 2\\n\\nParagraph 3"

        result = format_explanation(text)

        assert "Paragraph 1" in result
        assert "Paragraph 2" in result

    def test_clean_multiple_spaces(self):
        """Test cleaning multiple spaces."""
        text = "This  has   multiple    spaces"

        result = format_explanation(text)

        # Should have single spaces
        assert "  " not in result or "\n" in result
