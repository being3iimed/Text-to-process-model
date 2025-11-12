"""Modeler Agent - Generates BPMN 2.0 JSON models from parsed process descriptions."""

from typing import Optional, Dict, Any, Tuple, List
import json
import httpx
import re
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
    BPMN 2.0 JSON model with validation and optimization
    """

    def __init__(
        self, api_key: Optional[str] = None, load_prompt_from_file: bool = True
    ):
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
            print("[ModelerAgent] ❌ CRITICAL: Could not load prompt from file!")
            print(f"[ModelerAgent] Error: {e}")
            raise

    def generate_model(
        self, parsed_pseudocode: str, process_name: str = "process"
    ) -> Dict[str, Any]:
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

Generate a comprehensive BPMN 2.0 JSON model that can be imported into BPMN tools like Camunda Modeler or draw.io.

Return ONLY valid BPMN 2.0 JSON that follows the standard structure with:
- $type: "bpmn:Definitions"
- rootElements containing bpmn:Process
- flowElements containing all tasks, gateways, events, and sequence flows
- Proper element IDs and references"""

            # Invoke the agent
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": modeler_input}]}
            )

            # Extract content
            response_content = self._extract_content(result)

            # Extract JSON from response with multiple strategies
            json_str, explanation = extract_json_from_text(response_content)

            bpmn_json = None
            validation_result = None
            
            if json_str:
                bpmn_json = parse_json(json_str)
                
                # Validate and enhance BPMN model
                if bpmn_json:
                    validation_result = self._validate_bpmn_model(bpmn_json)
                    if validation_result["is_valid"]:
                        # Enhance the model with missing properties
                        bpmn_json = self._enhance_bpmn_model(bpmn_json)
                        print("[MODELER AGENT] ✓ BPMN model validated and enhanced")
                    else:
                        print(f"[MODELER AGENT] ⚠ Validation warnings: {validation_result['warnings']}")

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
                "validation": validation_result,
                "metadata": metadata,
                "process_name": process_name,
                "status": "success" if bpmn_json else "partial",
            }

            print("[MODELER AGENT] ✓ Model generation completed")
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

    def _validate_bpmn_model(self, bpmn_json: dict) -> Dict[str, Any]:
        """
        Validate BPMN 2.0 JSON structure.

        Args:
            bpmn_json: BPMN model to validate

        Returns:
            Validation result dictionary
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "element_counts": {},
        }

        try:
            # Check root structure
            if not isinstance(bpmn_json, dict):
                validation["is_valid"] = False
                validation["errors"].append("Root must be a dictionary")
                return validation

            if bpmn_json.get("$type") != "bpmn:Definitions":
                validation["warnings"].append("Missing bpmn:Definitions type")

            # Check rootElements
            root_elements = bpmn_json.get("rootElements", [])
            if not root_elements:
                validation["is_valid"] = False
                validation["errors"].append("Missing rootElements")
                return validation

            # Check process
            process = None
            for element in root_elements:
                if element.get("$type") == "bpmn:Process":
                    process = element
                    break

            if not process:
                validation["is_valid"] = False
                validation["errors"].append("No bpmn:Process found in rootElements")
                return validation

            # Count flow elements
            flow_elements = process.get("flowElements", [])
            element_types = {}
            
            for element in flow_elements:
                element_type = element.get("$type", "Unknown")
                element_types[element_type] = element_types.get(element_type, 0) + 1

            validation["element_counts"] = element_types

            # Validate start and end events
            start_events = [e for e in flow_elements if e.get("$type") == "bpmn:StartEvent"]
            end_events = [e for e in flow_elements if e.get("$type") == "bpmn:EndEvent"]

            if not start_events:
                validation["warnings"].append("No start events found")
            if not end_events:
                validation["warnings"].append("No end events found")

            # Validate sequence flows have source and target
            sequence_flows = [e for e in flow_elements if e.get("$type") == "bpmn:SequenceFlow"]
            invalid_flows = [
                f for f in sequence_flows 
                if not f.get("sourceRef") or not f.get("targetRef")
            ]
            
            if invalid_flows:
                validation["warnings"].append(
                    f"{len(invalid_flows)} sequence flows missing source or target references"
                )

            # Validate gateways have diverging/converging direction
            gateways = [e for e in flow_elements if "Gateway" in e.get("$type", "")]
            for gateway in gateways:
                if not gateway.get("gatewayDirection"):
                    validation["warnings"].append(
                        f"Gateway {gateway.get('id')} missing gatewayDirection"
                    )

        except Exception as e:
            validation["is_valid"] = False
            validation["errors"].append(f"Validation error: {str(e)}")

        return validation

    def _enhance_bpmn_model(self, bpmn_json: dict) -> dict:
        """
        Enhance BPMN model with missing properties.

        Args:
            bpmn_json: BPMN model to enhance

        Returns:
            Enhanced BPMN model
        """
        try:
            # Ensure definitions properties
            if not bpmn_json.get("id"):
                bpmn_json["id"] = "definitions-" + self._generate_id()
            
            if not bpmn_json.get("targetNamespace"):
                bpmn_json["targetNamespace"] = "http://bpmn.io/schema/bpmn"

            # Ensure process properties
            process = bpmn_json.get("rootElements", [{}])[0]
            if not process.get("id"):
                process["id"] = "process-" + self._generate_id()
            
            if not process.get("isExecutable"):
                process["isExecutable"] = True

            # Enhance flow elements with missing IDs
            flow_elements = process.get("flowElements", [])
            for i, element in enumerate(flow_elements):
                if not element.get("id"):
                    element_type = element.get("$type", "Element").replace("bpmn:", "")
                    element["id"] = f"{element_type}-{self._generate_id()}"

            print("[MODELER AGENT] ✓ Model enhanced with missing properties")
            return bpmn_json

        except Exception as e:
            print(f"[MODELER AGENT] ⚠ Enhancement error: {e}")
            return bpmn_json

    def _generate_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return str(uuid.uuid4())[:8]

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

    def save_results(
        self, process_name: str = "bpmn_model", parser_folder: str = None
    ) -> Dict[str, Path]:
        """
        Save modeler results to output folder with organized structure.

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
                json.dump(
                    self.last_result["bpmn_json"], f, indent=2, ensure_ascii=False
                )
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
        element_counts = self.last_result.get("validation", {}).get("element_counts", {})
        metadata_output = {
            "modeler_metadata": self.last_result["metadata"],
            "process_info": {
                "process_name": process_name,
                "bpmn_elements": len(
                    self.last_result.get("bpmn_json", {}).get("rootElements", [{}])[0].get(
                        "flowElements", []
                    )
                ),
                "element_types": element_counts,
            },
            "validation_status": self.last_result.get("validation", {}).get("is_valid", False),
            "parser_reference": parser_folder,
            "status": self.last_result["status"],
        }
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_output, f, indent=2, ensure_ascii=False, default=str)
        saved_files["metadata"] = metadata_file
        print(f"✓ Metadata saved to: {metadata_file}")

        # Save combined output
        output_json = modeler_output_dir / "output.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "bpmn_model": self.last_result["bpmn_json"],
                    "explanation": self.last_result["explanation"],
                    "metadata": self.last_result["metadata"],
                    "status": self.last_result["status"],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        saved_files["output"] = output_json
        print(f"✓ Comprehensive output saved to: {output_json}")

        return saved_files

    def get_last_output(self) -> Optional[Dict]:
        """
        Get the last modeling output.

        Returns:
            Last generated model or None
        """
        return self.last_result

    def get_bpmn_model(self) -> Optional[Dict]:
        """
        Get BPMN model from last generation.

        Returns:
            BPMN JSON model or None
        """
        if self.last_result:
            return self.last_result.get("bpmn_json")
        return None

    def get_validation_report(self) -> Optional[Dict]:
        """
        Get validation report from last generation.

        Returns:
            Validation report or None
        """
        if self.last_result:
            return self.last_result.get("validation")
        return None