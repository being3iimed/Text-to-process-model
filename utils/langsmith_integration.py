"""LangSmith Integration for Text to Process Model."""

import os
from typing import Optional


def setup_langsmith():
    """
    Setup LangSmith tracing and monitoring.
    
    Environment variables needed:
    - LANGSMITH_API_KEY: Your LangSmith API key
    - LANGSMITH_PROJECT: Project name (optional, defaults to "default")
    - LANGSMITH_ENDPOINT: API endpoint (optional)
    """
    
    # Get API key from environment
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT", "text-to-process-model")
    
    if api_key:
        # Enable tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        
        print(f"✓ LangSmith enabled - Project: {project}")
        return True
    else:
        print("⚠ LangSmith not configured (LANGSMITH_API_KEY not set)")
        return False


def example_with_langsmith():
    """Example of using LangSmith with the parser agent."""
    
    # Setup LangSmith first
    setup_langsmith()
    
    # Then import and use agents normally
    from agents.parser_agent import ParserAgent
    
    # ParserAgent will automatically be traced by LangSmith
    parser = ParserAgent()
    
    process_description = """
    Customer inquiry process: A customer contacts sales.
    Staff collects info and addresses questions.
    If interested, guide through product selection.
    """
    
    result = parser.parse(process_description)
    
    # All calls are automatically traced in LangSmith!
    return result


class LangSmithConfig:
    """Configuration manager for LangSmith."""
    
    def __init__(self):
        """Initialize LangSmith configuration."""
        self.api_key = os.getenv("LANGSMITH_API_KEY")
        self.project = os.getenv("LANGSMITH_PROJECT", "text-to-process-model")
        self.endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.enabled = bool(self.api_key)
    
    def enable(self):
        """Enable LangSmith tracing."""
        if not self.enabled:
            print("❌ LANGSMITH_API_KEY not set")
            return False
        
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = self.api_key
        os.environ["LANGCHAIN_PROJECT"] = self.project
        os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
        
        print(f"✓ LangSmith enabled:")
        print(f"  Project: {self.project}")
        print(f"  Endpoint: {self.endpoint}")
        return True
    
    def disable(self):
        """Disable LangSmith tracing."""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        print("✓ LangSmith disabled")
    
    def status(self) -> dict:
        """Get LangSmith status."""
        return {
            "enabled": self.enabled,
            "api_key_set": bool(self.api_key),
            "project": self.project,
            "endpoint": self.endpoint,
        }


def log_trace_info(operation: str, details: dict):
    """Log trace information for monitoring."""
    import json
    from datetime import datetime
    
    trace_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "details": details,
    }
    
    print(f"\n📍 Trace: {json.dumps(trace_data, indent=2)}")


if __name__ == "__main__":
    # Setup LangSmith
    config = LangSmithConfig()
    print("LangSmith Status:")
    print(config.status())
    
    # Enable it
    if config.enabled:
        config.enable()
        
        # Now run your workflows - they'll be auto-traced!
        from agents.orchestrator_agent import DeepAgent
        
        agent = DeepAgent()
        result = agent.run_complete_workflow(
            process_description="Simple customer process",
            process_name="test_process"
        )
        
        print("\n✓ Workflow complete - Check LangSmith for traces!")