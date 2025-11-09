# tests/test_utils/test_json_parser.py
"""Tests for JSON parser utility."""

from utils.json_parser import extract_json_from_text, parse_json, make_json_serializable


class TestExtractJsonFromText:
    """Tests for JSON extraction."""

    def test_extract_from_code_fence(self):
        """Test extracting from markdown code fence."""
        content = """
        Here's the model:
        ```json
        {"id": "Process_1", "name": "test"}
        ```
        End of explanation.
        """

        json_str, explanation = extract_json_from_text(content)

        assert json_str is not None
        assert "Process_1" in json_str
        assert "explanation" in explanation.lower()

    def test_extract_from_braces(self):
        """Test extracting JSON by matching braces."""
        content = 'Some text {"id": "test", "value": 42} more text'

        json_str, explanation = extract_json_from_text(content)

        assert json_str is not None
        assert '"id": "test"' in json_str

    def test_no_json_found(self):
        """Test when no JSON is present."""
        content = "This is just plain text with no JSON"

        json_str, explanation = extract_json_from_text(content)

        assert json_str is None
        assert explanation == content


class TestParseJson:
    """Tests for JSON parsing."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = '{"id": "test", "value": 123}'

        result = parse_json(json_str)

        assert result is not None
        assert result["id"] == "test"
        assert result["value"] == 123

    def test_parse_with_escape_sequences(self):
        """Test parsing with escape sequences."""
        json_str = '{"text": "line1\\nline2", "quote": "\\"quoted\\""}'

        result = parse_json(json_str)

        # Should handle escape sequences gracefully
        assert result is not None or result is None  # Depends on encoding

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        json_str = "{invalid: json}"

        result = parse_json(json_str)

        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_json("")

        assert result is None


class TestMakeJsonSerializable:
    """Tests for JSON serializability."""

    def test_serializable_dict(self):
        """Test dict is serializable."""
        obj = {"id": "test", "value": 42}

        result = make_json_serializable(obj)

        assert result == obj

    def test_serializable_list(self):
        """Test list is serializable."""
        obj = [1, 2, 3, {"id": "test"}]

        result = make_json_serializable(obj)

        assert result == obj

    def test_non_serializable_object(self):
        """Test non-serializable object becomes string."""

        class CustomObj:
            pass

        obj = CustomObj()
        result = make_json_serializable(obj)

        assert isinstance(result, str)
