"""Shared fixtures for all tests."""

import pytest
from unittest.mock import Mock, patch
import json
import os
from pathlib import Path

# Set test environment variables BEFORE importing agents
os.environ['MISTRAL_API_KEY'] = 'test-key-placeholder'
os.environ['PYTEST_CURRENT_TEST'] = 'yes'


@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables for all tests."""
    os.environ['MISTRAL_API_KEY'] = 'test-key-placeholder'
    yield


@pytest.fixture
def sample_pseudocode():
    """Sample pseudocode for testing."""
    return """
    START
        INPUT user_data
        IF user_data.valid THEN
            PROCESS user_data
            OUTPUT result
        ELSE
            OUTPUT error
        END IF
    END
    """


@pytest.fixture
def sample_parsed_output():
    """Expected parser output."""
    return {
        "steps": [
            {"type": "start", "id": "step_1"},
            {"type": "input", "id": "step_2", "value": "user_data"},
            {"type": "decision", "id": "step_3", "condition": "user_data.valid"},
            {"type": "process", "id": "step_4"},
            {"type": "output", "id": "step_5"},
            {"type": "end", "id": "step_6"}
        ]
    }


@pytest.fixture
def sample_bpmn_output():
    """Expected BPMN output."""
    return {
        "id": "Process_1",
        "elements": [
            {"id": "StartEvent_1", "type": "startEvent"},
            {"id": "Task_1", "type": "task", "name": "Process user_data"},
            {"id": "Gateway_1", "type": "exclusiveGateway"},
            {"id": "EndEvent_1", "type": "endEvent"}
        ]
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_api_response():
    """Mock API response."""
    return {
        "messages": [
            {
                "content": '```json\n{"id": "Process_1"}\n```',
                "role": "assistant"
            }
        ]
    }


@pytest.fixture
def mock_mistral_model():
    """Mock Mistral AI model."""
    model = Mock()
    model.invoke = Mock(return_value={"messages": [{"content": '```json\n{}\n```'}]})
    return model