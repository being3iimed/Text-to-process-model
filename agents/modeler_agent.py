"""Modeler Agent - Generates BPMN 2.0 JSON models from parsed process descriptions."""

from typing import Optional, Dict, Any
import json
import httpx
from pathlib import Path

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from config.settings import MISTRAL_API_KEY, MISTRAL_MODEL
from utils.file_handler import load_prompt, ensure_output_dir
from utils.json_parser import extract_json_from_text, parse_json
from utils.text_formatter import extract_metadata_from_response, format_explanation
from utils.error_handler import handle_http_error, handle_unexpected_error
from output.writer import OutputWriter


class ModelerAgent:
    """
    Modeler Sub-Agent.
    
    Converts parsed process descriptions (elements + pseudocode) into:
    BPMN 2.0 JSON model
    """
    
    def __init__(self, api_key: Optional[str] = None, load_prompt_from_file: bool = True):
        """
        Initialize the modeler agent.
        
        Args:
            api_key: Optional API key (uses config default if not provided)
            load_prompt_from_file: Whether to load prompt from modeler_prompt.md
        """
        self.api_key = api_key or MISTRAL_API_KEY
        
        # Always initialize these first
        self.last_result = None
        
        # Load prompt from file (required)
        self.prompt = self._load_prompt(load_prompt_from_file)
        print(f"[ModelerAgent] Using prompt: {len(self.prompt)} characters")
        
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
        print("[ModelerAgent] ✓ Agent initialized with real API")
        
        # Output writer
        try:
            output_dir = ensure_output_dir()
            self.writer = OutputWriter(output_dir)
        except Exception:
            self.writer = None
    
    def _load_prompt(self, load_from_file: bool = True) -> str:
        """
        Load modeler prompt from file (required).
        
        Args:
            load_from_file: Whether to load from file (always True)
            
        Returns:
            The system prompt string
            
        Raises:
            FileNotFoundError: If prompt file not found
        """
        try:
            # Load from file (required)
            prompt = load_prompt("modeler")
            print("[ModelerAgent] ✓ Loaded prompt from modeler_prompt.md")
            return prompt
        except Exception as e:
            print(f"[ModelerAgent] ❌ CRITICAL: Could not load prompt from file!")
            print(f"[ModelerAgent] Error: {e}")
            raise
    
    def generate_model(self, parsed_pseudocode: str, process_name: str = "process") -> Dict[str, Any]:
        """
        Generate BPMN 2.0 model from parsed pseudocode.
        
        Args:
            parsed_pseudocode: Pseudocode from parser (elements + pseudocode)
            process_name: Name of the process for file organization
            
        Returns:
            Dictionary with BPMN model and metadata
        """
        try:
            print("\n[MODELER AGENT] Generating BPMN 2.0 model...")
            
            # Prepare input for modeler
            modeler_input = f"""Based on this process pseudocode:

{parsed_pseudocode}

Generate a comprehensive BPMN 2.0 JSON model that can be imported into BPMN tools like Camunda Modeler or draw.io."""
            
            # Invoke the agent
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": modeler_input}]
            })
            
            # Extract content
            response_content = self._extract_content(result)
            
            # Extract JSON from response
            json_str, explanation = extract_json_from_text(response_content)
            
            bpmn_json = None
            if json_str:
                bpmn_json = parse_json(json_str)
            
            # Format explanation
            if explanation:
                explanation = format_explanation(explanation)
            
            # Extract metadata
            metadata = self._extract_metadata(result)
            
            # Store result
            self.last_result = {
                "bpmn_json": bpmn_json,
                "explanation": explanation,
                "raw_response": response_content,
                "metadata": metadata,
                "process_name": process_name,
                "status": "success"
            }
            
            print(f"[MODELER AGENT] ✓ Model generation completed")
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
    
    def save_results(self, process_name: str = "bpmn_model", parser_folder: str = None) -> Dict[str, Path]:
        """
        Save modeler results to output folder.
        
        Args:
            process_name: Name of the process
            parser_folder: Optional path to parser output folder (for reference)
            
        Returns:
            Dictionary with paths to saved files
        """
        if not self.last_result:
            print("[MODELER AGENT] No results to save. Run generate_model() first.")
            return {}
        
        # Create modeler output directory
        output_dir = ensure_output_dir()
        modeler_output_dir = output_dir / "modeler" / process_name
        modeler_output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Save BPMN JSON
        if self.last_result.get("bpmn_json"):
            json_file = modeler_output_dir / "bpmn_model.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(self.last_result["bpmn_json"], f, indent=2, ensure_ascii=False)
            saved_files["bpmn_json"] = json_file
            print(f"✓ BPMN JSON saved to: {json_file}")
        
        # Save explanation
        if self.last_result.get("explanation"):
            explanation_file = modeler_output_dir / "explanation.txt"
            with open(explanation_file, "w", encoding="utf-8") as f:
                f.write(self.last_result["explanation"])
            saved_files["explanation"] = explanation_file
            print(f"✓ Explanation saved to: {explanation_file}")
        
        # Save full response
        response_file = modeler_output_dir / "full_response.txt"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(self.last_result["raw_response"])
        saved_files["response"] = response_file
        print(f"✓ Full response saved to: {response_file}")
        
        # Save metadata
        metadata_file = modeler_output_dir / "metadata.json"
        metadata_output = {
            "modeler_metadata": self.last_result["metadata"],
            "process_info": {
                "process_name": process_name,
                "bpmn_elements": len(self.last_result.get("bpmn_json", {}).get("elements", [])),
                "bpmn_flows": len(self.last_result.get("bpmn_json", {}).get("flows", [])),
            },
            "parser_reference": parser_folder,
            "status": self.last_result["status"]
        }
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_output, f, indent=2, ensure_ascii=False, default=str)
        saved_files["metadata"] = metadata_file
        print(f"✓ Metadata saved to: {metadata_file}")
        
        # Save combined output
        output_json = modeler_output_dir / "output.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump({
                "bpmn_model": self.last_result["bpmn_json"],
                "explanation": self.last_result["explanation"],
                "metadata": self.last_result["metadata"],
                "status": self.last_result["status"]
            }, f, indent=2, ensure_ascii=False)
        saved_files["output"] = output_json
        print(f"✓ Output JSON saved to: {output_json}")
        
        return saved_files
    
    def get_last_output(self) -> Optional[Dict]:
        """
        Get the last modeling output.
        
        Returns:
            Last generated model or None
        """
        return self.last_result