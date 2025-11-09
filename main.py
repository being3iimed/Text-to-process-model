"""Orchestrator Agent Main Entry Point - Interactive Process Transformation."""

import argparse
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator_agent import OrchestratorAgent


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("🚀 Orchestrator AGENT - PROCESS TO BPMN TRANSFORMER")
    print("="*70)
    print("Transform natural language process descriptions into BPMN 2.0 models")
    print("="*70 + "\n")


def get_process_description_interactive() -> tuple:
    """
    Get process description interactively from user.
    
    Returns:
        Tuple of (process_description, process_name)
    """
    print("📝 PROCESS DESCRIPTION INPUT")
    print("-"*70)
    print("Enter your business process description.")
    print("You can write it in natural language (multiple lines).")
    print("When done, type 'END' on a new line.")
    print("-"*70 + "\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            # Handle piped input or EOF
            if not lines:
                print("❌ No input provided")
                return None, None
            break
        except KeyboardInterrupt:
            print("\n\n⚠️  Input cancelled by user")
            return None, None
    
    process_description = "\n".join(lines).strip()
    
    if not process_description:
        print("❌ Empty process description")
        return None, None
    
    print(f"\n✅ Received {len(process_description)} characters\n")
    
    # Get process name
    print("📛 PROCESS NAME")
    print("-"*70)
    process_name = input("Enter a name for this process (for organizing outputs): ").strip()
    
    if not process_name:
        # Use default based on length
        process_name = f"process_{len(process_description)}"
        print(f"Using default name: {process_name}")
    else:
        # Sanitize name
        process_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in process_name)
    
    print(f"✅ Process name: {process_name}\n")
    
    return process_description, process_name


def get_process_description_from_file(input_file: str) -> tuple:
    """
    Get process description from file.
    
    Args:
        input_file: Path to input file
        
    Returns:
        Tuple of (process_description, process_name)
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            process_description = f.read()
        
        # Extract process name from filename
        process_name = Path(input_file).stem
        
        return process_description, process_name
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return None, None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None, None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrator Agent - Transform process descriptions to BPMN 2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Interactive mode (terminal input)
  python main.py --input file.txt         # From file
  python main.py --content "description"  # From direct argument
  python main.py --verbose                # With detailed output
        """
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to input file with process description"
    )
    parser.add_argument(
        "--content",
        "-c",
        type=str,
        default=None,
        help="Direct process description content"
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help="Process name for organizing outputs"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output workflow result as JSON"
    )
    
    args = parser.parse_args()
    
    try:
        print_header()
        
        # Determine input source
        if args.content:
            # Direct content
            process_description = args.content
            process_name = args.name or "process_from_content"
            print(f"📄 Input: Direct content ({len(process_description)} chars)\n")
        
        elif args.input:
            # From file
            process_description, name_from_file = get_process_description_from_file(args.input)
            if process_description is None:
                return 1
            process_name = args.name or name_from_file
            print(f"📄 Input: {args.input}\n")
        
        else:
            # Interactive input
            process_description, process_name = get_process_description_interactive()
            if process_description is None:
                return 1
        
        # Initialize Orchestrator agent
        print("\n🔄 Initializing Orchestrator Agent...\n")
        Orchestrator_agent = OrchestratorAgent()
        
        # Run complete workflow
        result = Orchestrator_agent.run_complete_workflow(
            process_description=process_description,
            process_name=process_name
        )
        
        # Handle results
        if result["status"] == "success":
            print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!\n")
            
            if args.verbose:
                print("\n🔍 DETAILED RESULTS:")
                print("-"*70)
                print(json.dumps(result, indent=2, default=str))
            
            if args.output_json:
                print("\n📊 RESULTS (JSON):")
                print(json.dumps(result, indent=2, default=str))
            
            print("\n📂 YOUR FILES ARE READY:")
            print("-"*70)
            print(f"Parser output: output/parser/{process_name}/")
            print(f"BPMN output:   output/modeler/{process_name}/bpmn_model.json")
            print("\n💡 Next steps:")
            print("1. View the BPMN model: cat output/modeler/{process_name}/bpmn_model.json")
            print("2. Import to Camunda Modeler or draw.io")
            print("3. View metadata: cat output/modeler/{process_name}/metadata.json")
            
            return 0
        else:
            print(f"\n❌ WORKFLOW FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Step: {result.get('step', 'unknown')}")
            
            if args.verbose:
                print(f"\nDetails:\n{json.dumps(result, indent=2, default=str)}")
            
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())