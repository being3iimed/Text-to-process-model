"""Parser Agent - Converts natural language process descriptions to pseudocode."""

from typing import Optional, Dict, Any, List
import json
import httpx
import re
from pathlib import Path

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import (
    MISTRAL_API_KEY, MISTRAL_MODEL, 
    GOOGLE_API_KEY, GOOGLE_MODEL,
    DEFAULT_PROVIDER
)
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
        self, 
        api_key: Optional[str] = None, 
        load_prompt_from_file: bool = True,
        provider: str = DEFAULT_PROVIDER
    ):
        """
        Initialize the parser agent.

        Args:
            api_key: Optional API key (uses config default if not provided)
            load_prompt_from_file: Whether to load prompt from parser_prompt.md
            provider: AI provider to use ("mistral" or "google")
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        # Always initialize these first
        self.last_result = None

        # Load prompt from file (required)
        self.prompt = self._load_prompt(load_prompt_from_file)
        print(f"[ParserAgent] Using prompt: {len(self.prompt)} characters")

        # Initialize Model based on provider
        if self.provider == "google":
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            self.model = ChatGoogleGenerativeAI(
                google_api_key=GOOGLE_API_KEY,
                model=GOOGLE_MODEL,
                temperature=0.05,
                convert_system_message_to_human=True
            )
            print(f"[ParserAgent] Initialized with Google GenAI ({GOOGLE_MODEL})")
            
        else: # Default to Mistral
            self.api_key = self.api_key or MISTRAL_API_KEY
            self.model = ChatMistralAI(
                api_key=self.api_key,
                model=MISTRAL_MODEL,
                temperature=0.05,
            )
            print(f"[ParserAgent] Initialized with Mistral AI ({MISTRAL_MODEL})")

        # Create the agent with loaded prompt
        self.agent = create_agent(
            self.model,
            tools=[],
            system_prompt=self.prompt,
        )

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
        # Pattern 3: XML-style tags (Prioritize these for new prompt)
        if section_name == "elements":
            xml_pattern = r"<elements>\n?(.*?)</elements>"
        elif section_name == "pseudocode":
            xml_pattern = r"<pseudocode>\n?(.*?)</pseudocode>"
        elif section_name == "validation":
            xml_pattern = r"<validation>\n?(.*?)</validation>"
        else:
            xml_pattern = None

        if xml_pattern:
            match = re.search(xml_pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback patterns for backward compatibility
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
            pattern1 = rf"#{1,6}\s*{re.escape(term)}.*?\n```(?:pseudocode|bpmn|text)?\n?(.*?)```"
            match = re.search(pattern1, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # Pattern 2: Markdown header without code block
            pattern2 = rf"#{1,6}\s*{re.escape(term)}.*?\n(.*?)(?=\n#{1,6}|\Z)"
            match = re.search(pattern2, content, re.IGNORECASE | re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                # Remove code block markers if present
                extracted = re.sub(r'^```(?:pseudocode|bpmn|text)?\n?', '', extracted)
                extracted = re.sub(r'\n?```$', '', extracted)
                return extracted.strip()

        # Fallback for pseudocode: look for code block directly if no header found
        if section_name == "pseudocode":
            # Look for ```pseudocode or ```bpmn blocks
            code_block_pattern = r"```(?:pseudocode|bpmn)\n?(.*?)```"
            match = re.search(code_block_pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

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

        # Regex to parse lines like: Type("Name") - Reason
        # e.g., userTask("Approve") - Human decision
        element_pattern = re.compile(r"^(\w+)\(\"([^\"]+)\"\)\s*-\s*(.*)$")

        for line in elements_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            match = element_pattern.match(line)
            if match:
                elem_type, elem_name, reason = match.groups()
                full_entry = f"{elem_type}(\"{elem_name}\") - {reason}"

                # Categorize based on type
                if "Task" in elem_type:
                    structured["tasks"].append(full_entry)
                elif "Gateway" in elem_type or elem_type in ["if", "else", "AND", "OR"]:
                    structured["gateways"].append(full_entry)
                elif "Event" in elem_type and "Boundary" not in elem_type:
                    structured["events"].append(full_entry)
                elif "Boundary" in elem_type:
                    structured["boundary_events"].append(full_entry)
                elif "SubProcess" in elem_type or "subProcess" in elem_type:
                    structured["subprocesses"].append(full_entry)
                else:
                    # Fallback for unknown types, put in tasks or events?
                    # Let's put in tasks for now as generic
                    structured["tasks"].append(full_entry)
            else:
                # Handle legacy format or unstructured lines if needed
                # For now, ignore or log?
                pass

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
            "provider": self.provider,
            "model": GOOGLE_MODEL if self.provider == "google" else MISTRAL_MODEL,
            "temperature": 0.2,
            "api_key_set": bool(self.api_key) or bool(GOOGLE_API_KEY),
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