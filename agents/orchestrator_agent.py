"""Orchestrator Agent Orchestrator - Complete workflow management."""

from typing import Optional, Dict, Any

from agents.parser_agent import ParserAgent
from agents.modeler_agent import ModelerAgent
from utils.file_handler import ensure_output_dir


class OrchestratorAgent:
    """
    Orchestrator Agent Orchestrator.
    
    Manages the complete workflow:
    1. Parse natural language process description
    2. Generate BPMN 2.0 model
    3. Organize outputs in output folder
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Orchestrator agent orchestrator.
        
        Args:
            api_key: Optional API key (uses config default if not provided)
        """
        print("[OrchestratorAgent] Initializing...")
        
        # Initialize sub-agents with API key
        self.parser_agent = ParserAgent(api_key=api_key)
        self.modeler_agent = ModelerAgent(api_key=api_key)
        
        # Ensure output directory exists
        self.output_dir = ensure_output_dir()
    
    def run_complete_workflow(self, process_description: str, process_name: str) -> Dict[str, Any]:
        """
        Run complete workflow from description to BPMN model.
        
        Args:
            process_description: Natural language process description
            process_name: Name for organizing outputs
            
        Returns:
            Dictionary with all results and file paths
        """
        try:
            print("\n" + "="*70)
            print("Orchestrator AGENT WORKFLOW - COMPLETE PROCESS TRANSFORMATION")
            print("="*70)
            
            # Step 1: Parse the process description
            print("\n" + "-"*70)
            print("STEP 1: PARSING PROCESS DESCRIPTION")
            print("-"*70)
            print(f"\n📝 Process Name: {process_name}")
            print(f"📄 Input: {len(process_description)} characters")
            
            parser_result = self.parser_agent.parse(process_description)
            
            if parser_result["status"] != "success":
                print(f"\n❌ Parser failed: {parser_result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "error": f"Parser failed: {parser_result.get('error')}",
                    "step": "parsing"
                }
            
            print(f"\n✅ Parser Status: {parser_result['status']}")
            print(f"📊 Elements extracted:")
            print("-" * 70)
            print(parser_result["elements"][:500] + ("..." if len(parser_result["elements"]) > 500 else ""))
            
            # Save parser results
            print(f"\n💾 Saving parser results...")
            parser_files = self.parser_agent.save_results(process_name=process_name)
            print(f"✓ Parser output saved to: output/parser/{process_name}/")
            
            # Step 2: Generate BPMN model from parsed output
            print("\n" + "-"*70)
            print("STEP 2: GENERATING BPMN 2.0 MODEL")
            print("-"*70)
            
            # Use full response as input to modeler
            parsed_pseudocode = parser_result["raw_response"]
            
            modeler_result = self.modeler_agent.generate_model(
                parsed_pseudocode, 
                process_name=process_name
            )
            
            if modeler_result["status"] != "success":
                print(f"\n❌ Modeler failed: {modeler_result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "error": f"Modeler failed: {modeler_result.get('error')}",
                    "step": "modeling",
                    "parser_results": parser_result
                }
            
            print(f"\n✅ Modeler Status: {modeler_result['status']}")
            
            if modeler_result.get("bpmn_json"):
                bpmn = modeler_result["bpmn_json"]
                print(f"📐 BPMN Model:")
                print(f"  - Process ID: {bpmn.get('id', 'N/A')}")
                print(f"  - Elements: {len(bpmn.get('elements', []))} items")
                print(f"  - Flows: {len(bpmn.get('flows', []))} connections")
            
            # Save modeler results
            print(f"\n💾 Saving modeler results...")
            modeler_files = self.modeler_agent.save_results(
                process_name=process_name,
                parser_folder=process_name
            )
            print(f"✓ Modeler output saved to: output/modeler/{process_name}/")
            
            # Step 3: Generate summary
            print("\n" + "="*70)
            print("WORKFLOW COMPLETE - SUMMARY")
            print("="*70)
            
            summary = {
                "status": "success",
                "process_name": process_name,
                "parser": {
                    "status": parser_result["status"],
                    "output_folder": f"output/parser/{process_name}",
                    "files_saved": list(parser_files.keys()),
                    "metadata": parser_result.get("metadata", {})
                },
                "modeler": {
                    "status": modeler_result["status"],
                    "output_folder": f"output/modeler/{process_name}",
                    "files_saved": list(modeler_files.keys()),
                    "metadata": modeler_result.get("metadata", {})
                }
            }
            
            print("\n📊 PARSER OUTPUT:")
            print("-" * 70)
            print(f"Status: {summary['parser']['status']}")
            print(f"Folder: {summary['parser']['output_folder']}")
            print(f"Files: {', '.join(summary['parser']['files_saved'])}")
            
            print("\n📐 MODELER OUTPUT:")
            print("-" * 70)
            print(f"Status: {summary['modeler']['status']}")
            print(f"Folder: {summary['modeler']['output_folder']}")
            print(f"Files: {', '.join(summary['modeler']['files_saved'])}")
            
            print("\n📁 OUTPUTS ORGANIZED AT:")
            print("-" * 70)
            print(f"output/")
            print(f"├── parser/{process_name}/")
            print(f"│   ├── elements.txt")
            print(f"│   ├── pseudocode.txt")
            print(f"│   ├── full_response.txt")
            print(f"│   ├── metadata.json")
            print(f"│   └── output.json")
            print(f"└── modeler/{process_name}/")
            print(f"    ├── bpmn_model.json          ← BPMN 2.0 (import to tools)")
            print(f"    ├── explanation.txt")
            print(f"    ├── metadata.json")
            print(f"    └── output.json")
            
            print("\n" + "="*70)
            
            return summary
            
        except Exception as e:
            print(f"\n❌ Error in workflow: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "type": type(e).__name__
            }
    
    def get_sub_agent_status(self) -> Dict[str, Dict]:
        """
        Get status of sub-agents.
        
        Returns:
            Status information from both sub-agents
        """
        return {
            "parser_agent": {
                "last_result": self.parser_agent.last_result,
            },
            "modeler_agent": {
                "last_result": self.modeler_agent.last_result,
            }
        }