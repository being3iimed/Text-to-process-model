#!/usr/bin/env python
"""
Standalone script to run the Modeler Agent.

Generates BPMN 2.0 JSON models from parsed process descriptions.

Usage:
    python run_modeler.py --input input/parser_output.txt
    python run_modeler.py --input output/parser/my_process/parsed_output.txt
    python run_modeler.py --provider google
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.modeler_agent import ModelerAgent
from utils.file_handler import load_input_content


def print_results(result: dict) -> None:
    """Pretty print modeler results."""
    print("\n" + "=" * 70)
    print("MODELER AGENT RESULTS")
    print("=" * 70)

    print(f"\n📊 Status: {result.get('status', 'unknown')}")

    validation = result.get("validation", {})
    if validation:
        print(f"✅ Valid BPMN: {validation.get('is_valid', False)}")
        if validation.get("warnings"):
            print(f"⚠️ Warnings: {len(validation['warnings'])}")
            for w in validation["warnings"]:
                print(f"  - {w}")
    
    print("\n📝 Explanation:")
    print("-" * 70)
    print(result.get("explanation", "No explanation provided")[:500] + "...")

    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Modeler Agent - Generate BPMN 2.0 JSON from pseudocode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_modeler.py --input input/parser_output.txt
  python run_modeler.py --save my_process_model
  python run_modeler.py --provider google
        """,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to input file with parsed pseudocode",
    )
    parser.add_argument(
        "--save",
        "-s",
        type=str,
        default="bpmn_model",
        help="Folder name to save results (default: bpmn_model)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        type=str,
        default="mistral",
        choices=["mistral", "google"],
        help="AI provider to use (default: mistral)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--raw", "-r", action="store_true", help="Print raw JSON output"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save results to files"
    )

    args = parser.parse_args()

    try:
        print(f"\n🚀 Initializing Modeler Agent (Provider: {args.provider})...\n")
        modeler_agent = ModelerAgent(provider=args.provider)

        # Load input
        input_path = args.input
        if not input_path:
            # Try default location
            default_path = Path("input/parser_output.txt")
            if default_path.exists():
                input_path = str(default_path)
            else:
                print("❌ Error: No input file provided and default input/parser_output.txt not found.")
                return 1

        print(f"📄 Loading input from: {input_path}")
        parsed_pseudocode = load_input_content(input_path)
        print(f"   Loaded {len(parsed_pseudocode)} chars")

        print("\n⏳ Generating BPMN model...\n")

        # Run modeler
        result = modeler_agent.generate_model(parsed_pseudocode, process_name=args.save)

        # Print results
        if args.raw:
            print(json.dumps(result, indent=2, default=str))
        else:
            print_results(result)

        # Print verbose info if requested
        if args.verbose:
            print("\n🔍 Verbose Information:")
            print("-" * 70)
            print(f"Raw Response:\n{result.get('raw_response', 'N/A')[:1000]}")
            if result.get("metadata"):
                print(
                    f"\nMetadata:\n{json.dumps(result['metadata'], indent=2, default=str)}"
                )

        # Save results if not disabled
        if not args.no_save:
            print("\n💾 Saving results...")
            saved_files = modeler_agent.save_results(process_name=args.save)
            print(f"\n✅ Results saved to: output/modeler/{args.save}/")
            print("\nFiles saved:")
            for file_type, file_path in saved_files.items():
                print(f"  - {file_type}: {file_path.name}")
        else:
            print("\n⏭️  Skipping file save (--no-save flag)")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
