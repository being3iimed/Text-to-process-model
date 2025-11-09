"""Parser Agent - Converts natural language process descriptions to pseudocode."""

from typing import Optional, Dict, Any
import json
import httpx
import re
from pathlib import Path

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from config.settings import MISTRAL_API_KEY, MISTRAL_MODEL
from utils.file_handler import load_prompt, ensure_output_dir
from utils.text_formatter import extract_metadata_from_response
from utils.error_handler import handle_http_error, handle_unexpected_error


class ParserAgent:
    """
    Parser Sub-Agent.
    
    Converts natural language process descriptions into:
    - Structured process elements (tasks, events, gateways)
    - Pseudocode representation
    """
    
    def __init__(self, api_key: Optional[str] = None, load_prompt_from_file: bool = True):
        """
        Initialize the parser agent.
        
        Args:
            api_key: Optional API key (uses config default if not provided)
            load_prompt_from_file: Whether to load prompt from parser_prompt.md
        """
        self.api_key = api_key or MISTRAL_API_KEY
        
        # Always initialize these first
        self.last_result = None
        
        # Load prompt from file (required)
        self.prompt = self._load_prompt(load_prompt_from_file)
        print(f"[ParserAgent] Using prompt: {len(self.prompt)} characters")
        
        # Initialize Mistral model
        self.model = ChatMistralAI(
            api_key=self.api_key,
            model=MISTRAL_MODEL,
            temperature=0.2,
        )
        
        # Create the agent with loaded prompt
        self.agent = create_agent(
            self.model,
            tools=[],
            system_prompt=self.prompt,
        )
        print("[ParserAgent] ✓ Agent initialized with real API")
    
    def _load_prompt(self, load_from_file: bool = True) -> str:
        """
        Load parser prompt from file (required).
        
        Args:
            load_from_file: Whether to load from file (always True)
            
        Returns:
            The system prompt string
            
        Raises:
            FileNotFoundError: If prompt file not found
        """
        try:
            # Load from file (required)
            prompt = load_prompt("parser")
            print("[ParserAgent] ✓ Loaded prompt from parser_prompt.md")
            return prompt
        except Exception as e:
            print(f"[ParserAgent] ❌ CRITICAL: Could not load prompt from file!")
            print(f"[ParserAgent] Error: {e}")
            raise
    
    def parse(self, process_description: str) -> Dict[str, Any]:
        """
        Parse natural language process description into structured elements and pseudocode.
        
        Args:
            process_description: Natural language process description
            
        Returns:
            Dictionary with elements, pseudocode, and metadata
        """
        try:
            print("\n[PARSER AGENT] Parsing process description...")
            
            # Invoke the agent
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": process_description}]
            })
            
            # Extract content
            response_content = self._extract_content(result)
            
            # Extract elements and pseudocode
            elements, pseudocode = self._extract_elements_and_pseudocode(response_content)
            
            # Extract metadata from the full result
            metadata = self._extract_metadata(result)
            
            # Store result
            self.last_result = {
                "elements": elements,
                "pseudocode": pseudocode,
                "raw_response": response_content,
                "metadata": metadata,
                "status": "success"
            }
            
            print(f"[PARSER AGENT] ✓ Parsing completed")
            return self.last_result
            
        except httpx.HTTPStatusError as e:
            handle_http_error(e)
        except Exception as e:
            handle_unexpected_error(e)
    
    def _extract_content(self, result: Any) -> str:
        """
        Extract response content from agent result.
        
        Args:
            result: Full result from agent invocation
            
        Returns:
            String content from the response
        """
        if isinstance(result, dict) and "messages" in result:
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    return last_message.get("content", str(result))
                else:
                    if hasattr(last_message, "content"):
                        return last_message.content
                    return str(last_message)
        
        return str(result)
    
    def _extract_metadata(self, result: dict) -> Dict[str, Any]:
        """
        Extract metadata from agent result (tokens, model, timestamps).
        
        Args:
            result: Full result from agent invocation
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "model": MISTRAL_MODEL,
            "temperature": 0.2,
            "api_key_set": self.api_key != "test-key-placeholder",
        }
        
        # Extract using utility function
        try:
            if isinstance(result, dict) and "messages" in result:
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    extracted = extract_metadata_from_response(last_msg)
                    metadata.update(extracted)
        except Exception as e:
            metadata["extraction_error"] = str(e)
        
        return metadata
    
    def _extract_elements_and_pseudocode(self, content: str) -> tuple:
        """
        Extract elements and pseudocode sections from response.
        
        Args:
            content: Response content
            
        Returns:
            Tuple of (elements_text, pseudocode_text)
        """
        # Extract elements section
        elements_match = re.search(r'<elements>(.*?)</elements>', content, re.DOTALL)
        elements_text = elements_match.group(1).strip() if elements_match else "Not extracted"
        
        # Extract pseudocode section
        pseudocode_match = re.search(r'<pseudocode>(.*?)</pseudocode>', content, re.DOTALL)
        pseudocode_text = pseudocode_match.group(1).strip() if pseudocode_match else "Not extracted"
        
        return elements_text, pseudocode_text
    
    def save_results(self, process_name: str = "parsed_process") -> Dict[str, Path]:
        """
        Save parser results to output folder.
        
        Args:
            process_name: Name for the output folder
            
        Returns:
            Dictionary with paths to saved files
        """
        if not self.last_result:
            print("[PARSER AGENT] No results to save. Run parse() first.")
            return {}
        
        # Create parser output directory
        output_dir = ensure_output_dir()
        parser_output_dir = output_dir / "parser" / process_name
        parser_output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Save elements
        elements_file = parser_output_dir / "elements.txt"
        with open(elements_file, "w", encoding="utf-8") as f:
            f.write(self.last_result["elements"])
        saved_files["elements"] = elements_file
        print(f"✓ Elements saved to: {elements_file}")
        
        # Save pseudocode
        pseudocode_file = parser_output_dir / "pseudocode.txt"
        with open(pseudocode_file, "w", encoding="utf-8") as f:
            f.write(self.last_result["pseudocode"])
        saved_files["pseudocode"] = pseudocode_file
        print(f"✓ Pseudocode saved to: {pseudocode_file}")
        
        # Save full response
        response_file = parser_output_dir / "full_response.txt"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(self.last_result["raw_response"])
        saved_files["response"] = response_file
        print(f"✓ Full response saved to: {response_file}")
        
        # Save metadata
        metadata_file = parser_output_dir / "metadata.json"
        metadata_output = {
            "parser_metadata": self.last_result["metadata"],
            "process_info": {
                "elements_count": len(self.last_result["elements"].split('\n')),
                "pseudocode_lines": len(self.last_result["pseudocode"].split('\n')),
            },
            "status": self.last_result["status"]
        }
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_output, f, indent=2, ensure_ascii=False, default=str)
        saved_files["metadata"] = metadata_file
        print(f"✓ Metadata saved to: {metadata_file}")
        
        # Save structured output (combined)
        output_json = parser_output_dir / "output.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump({
                "elements": self.last_result["elements"],
                "pseudocode": self.last_result["pseudocode"],
                "metadata": self.last_result["metadata"],
                "status": self.last_result["status"]
            }, f, indent=2, ensure_ascii=False)
        saved_files["output"] = output_json
        print(f"✓ Output JSON saved to: {output_json}")
        
        return saved_files
    
    def get_last_output(self) -> Optional[Dict]:
        """
        Get the last parsing output.
        
        Returns:
            Last parsed result or None
        """
        return self.last_result