"""Parser Agent - Converts natural language process descriptions to pseudocode."""

from typing import Optional, Dict, Any, List
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

    def __init__(
        self, api_key: Optional[str] = None, load_prompt_from_file: bool = True
    ):
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
            temperature=0.05,
        )

        # Create the agent with loaded prompt
        self.agent = create_agent(
            self.model,
            tools=[],
            system_prompt=self.prompt,
        )
        print("[ParserAgent] Agent initialized with real API")

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
            print("[ParserAgent] CRITICAL: Could not load prompt from file!")
            print(f"[ParserAgent] Error: {e}")
            raise

    def parse(self, process_description: str) -> Dict[str, Any]:
        """
        Parse natural language process description into structured elements and pseudocode.

        Args:
            process_description: Natural language process description

        Returns:
            Dictionary with elements, pseudocode, validation, and metadata
        """
        try:
            print("\n[PARSER AGENT] Parsing process description...")

            # Invoke the agent
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": process_description}]}
            )

            # Extract content
            response_content = self._extract_content(result)

            # Extract all three sections
            elements = self._extract_section(response_content, "elements")
            validation = self._extract_section(response_content, "validation")
            pseudocode = self._extract_section(response_content, "pseudocode")

            # Parse structured elements from elements section
            structured_elements = self._parse_structured_elements(elements)

            # Extract metadata from the full result
            metadata = self._extract_metadata(result)

            # Store result
            self.last_result = {
                "elements": elements,
                "structured_elements": structured_elements,
                "validation": validation,
                "pseudocode": pseudocode,
                "raw_response": response_content,
                "metadata": metadata,
                "status": "success",
            }

            print("[PARSER AGENT] ✓ Parsing completed")
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

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract a named section from response content.

        Args:
            content: Full response content
            section_name: Section name (elements, validation, pseudocode)

        Returns:
            Section content or empty string if not found
        """
        # Handle different section names
        if section_name == "elements":
            search_terms = ["Summary of Elements", "SUMMARY OF ELEMENTS", "Elements"]
        elif section_name == "pseudocode":
            search_terms = ["BPMN Pseudocode", "Pseudocode", "PSEUDOCODE"]
        elif section_name == "validation":
            search_terms = ["COMPLIANCE CHECKS", "Validation", "VALIDATION"]
        else:
            search_terms = [section_name]

        # Try multiple patterns
        for term in search_terms:
            # Pattern 1: Markdown header with optional code block
            pattern1 = rf"###\s*{re.escape(term)}.*?\n```(?:pseudocode|bpmn|text)?\n?(.*?)```"
            match = re.search(pattern1, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # Pattern 2: Markdown header without code block
            pattern2 = rf"###\s*{re.escape(term)}.*?\n(.*?)(?=\n###|\Z)"
            match = re.search(pattern2, content, re.IGNORECASE | re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                # Remove code block markers if present
                extracted = re.sub(r'^```(?:pseudocode|bpmn|text)?\n?', '', extracted)
                extracted = re.sub(r'\n?```$', '', extracted)
                return extracted.strip()

        return ""

    def _parse_structured_elements(self, elements_text: str) -> Dict[str, List[str]]:
        """
        Parse structured elements from elements section.

        Args:
            elements_text: Elements section text

        Returns:
            Dictionary with tasks, gateways, events, boundary_events, subprocesses
        """
        structured = {
            "tasks": [],
            "gateways": [],
            "events": [],
            "boundary_events": [],
            "subprocesses": [],
        }

        if not elements_text:
            return structured

        # Extract tasks
        tasks_match = re.search(
            r"TASKS?:\s*\n(.*?)(?=\nGATEWAYS?:|\nEVENTS?:|\Z)", 
            elements_text, 
            re.DOTALL | re.IGNORECASE
        )
        if tasks_match:
            task_lines = tasks_match.group(1).strip().split("\n")
            structured["tasks"] = [
                line.strip() for line in task_lines 
                if line.strip() and line.strip().startswith("-")
            ]

        # Extract gateways
        gateways_match = re.search(
            r"GATEWAYS?:\s*\n(.*?)(?=\nEVENTS?:|\nBOUNDARY|\nSUBPROCESSES?:|\Z)",
            elements_text,
            re.DOTALL | re.IGNORECASE
        )
        if gateways_match:
            gateway_lines = gateways_match.group(1).strip().split("\n")
            structured["gateways"] = [
                line.strip() for line in gateway_lines 
                if line.strip() and line.strip().startswith("-")
            ]

        # Extract events
        events_match = re.search(
            r"EVENTS?:\s*\n(.*?)(?=\nBOUNDARY|\nSUBPROCESSES?:|\Z)", 
            elements_text, 
            re.DOTALL | re.IGNORECASE
        )
        if events_match:
            event_lines = events_match.group(1).strip().split("\n")
            structured["events"] = [
                line.strip() for line in event_lines 
                if line.strip() and line.strip().startswith("-")
            ]

        # Extract boundary events
        boundary_match = re.search(
            r"BOUNDARY\s+EVENTS?:\s*\n(.*?)(?=\nSUBPROCESSES?:|\Z)", 
            elements_text, 
            re.DOTALL | re.IGNORECASE
        )
        if boundary_match:
            boundary_lines = boundary_match.group(1).strip().split("\n")
            structured["boundary_events"] = [
                line.strip()
                for line in boundary_lines
                if line.strip() and line.strip().startswith("-")
            ]

        # Extract subprocesses
        subprocess_match = re.search(
            r"SUBPROCESSES?:\s*\n(.*?)$", 
            elements_text, 
            re.DOTALL | re.IGNORECASE
        )
        if subprocess_match:
            subprocess_lines = subprocess_match.group(1).strip().split("\n")
            structured["subprocesses"] = [
                line.strip()
                for line in subprocess_lines
                if line.strip() and line.strip().startswith("-")
            ]

        return structured

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

    def save_results(self, process_name: str = "parsed_process") -> Dict[str, Path]:
        """
        Save parser results to output folder with organized structure.
        Now saves only 3 files: metadata.json, full_response.txt, and parsed_output.txt

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

        # 1. Save combined elements & pseudocode
        parsed_output_file = parser_output_dir / "parsed_output.txt"
        with open(parsed_output_file, "w", encoding="utf-8") as f:
            f.write("### SUMMARY OF ELEMENTS\n")
            f.write("-" * 80 + "\n")
            f.write(self.last_result["elements"] if self.last_result["elements"] else "No elements extracted")
            f.write("\n\n")
            
            f.write("### BPMN PSEUDOCODE\n")
            f.write("-" * 80 + "\n")
            f.write(self.last_result["pseudocode"] if self.last_result["pseudocode"] else "No pseudocode extracted")
            f.write("\n\n")
        
        saved_files["parsed_output"] = parsed_output_file
        print(f" Parsed output saved to: {parsed_output_file}")

        # 2. Save full response
        response_file = parser_output_dir / "full_response.txt"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(self.last_result["raw_response"])
        saved_files["full_response"] = response_file
        print(f" Full response saved to: {response_file}")

        # 3. Save metadata with process statistics
        metadata_file = parser_output_dir / "metadata.json"
        metadata_output = {
            "parser_metadata": self.last_result["metadata"],
            "process_info": {
                "tasks_count": len(self.last_result["structured_elements"]["tasks"]),
                "gateways_count": len(self.last_result["structured_elements"]["gateways"]),
                "events_count": len(self.last_result["structured_elements"]["events"]),
                "boundary_events_count": len(
                    self.last_result["structured_elements"]["boundary_events"]
                ),
                "subprocesses_count": len(
                    self.last_result["structured_elements"]["subprocesses"]
                ),
                "pseudocode_lines": len(self.last_result["pseudocode"].split("\n")) if self.last_result["pseudocode"] else 0,
                "elements_extracted": bool(self.last_result["elements"]),
                "pseudocode_extracted": bool(self.last_result["pseudocode"]),
            },
            "structured_elements": self.last_result["structured_elements"],
            "status": self.last_result["status"],
        }
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_output, f, indent=2, ensure_ascii=False, default=str)
        saved_files["metadata"] = metadata_file
        print(f"✓ Metadata saved to: {metadata_file}")

        print(f"\n[PARSER AGENT] All results saved to: {parser_output_dir}")
        return saved_files

    def get_last_output(self) -> Optional[Dict]:
        """
        Get the last parsing output.

        Returns:
            Last parsed result or None
        """
        return self.last_result

    def get_structured_elements(self) -> Optional[Dict[str, List[str]]]:
        """
        Get structured elements from last parsing.

        Returns:
            Structured elements dictionary or None
        """
        if self.last_result:
            return self.last_result.get("structured_elements")
        return None