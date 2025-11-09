#!/usr/bin/env python
"""
Standalone script to run the Modeler Agent.

Converts parsed process pseudocode into BPMN 2.0 JSON models.

Usage:
    python run_modeler.py --parser my_process
    python run_modeler.py --input parser_output.txt --save my_bpmn
    python run_modeler.py --content "<pseudocode>...</pseudocode>"
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.modeler_agent import ModelerAgent


def load_parser_output(process_name: str) -> str:
    """
    Load output from parser results.

    Args:
        process_name: Name of the parsed process folder

    Returns:
        Full response content from parser
    """
    parser_output_path = Path("output/parser") / process_name / "full_response.txt"

    if not parser_output_path.exists():
        raise FileNotFoundError(
            f"Parser output not found at: {parser_output_path}\n"
            f"Did you run: python run_parser.py --save {process_name}?"
        )

    with open(parser_output_path, "r", encoding="utf-8") as f:
        return f.read()


def print_results(result: dict) -> None:
    """Pretty print modeler results."""
    print("\n" + "=" * 70)
    print("MODELER AGENT RESULTS")
    print("=" * 70)

    print(f"\n📊 Status: {result.get('status', 'unknown')}")

    print("\n📐 BPMN Model Summary:")
    print("-" * 70)
    model = result.get("bpmn_json")
    if model:
        print(f"Process ID: {model.get('id', 'N/A')}")
        print(f"Process Name: {model.get('name', 'N/A')}")
        print(f"Elements: {len(model.get('elements', []))} items")
        print(f"Flows: {len(model.get('flows', []))} connections")

        # Show element types
        elements = model.get("elements", [])
        if elements:
            types = {}
            for elem in elements:
                elem_type = elem.get("type", "unknown")
                types[elem_type] = types.get(elem_type, 0) + 1
            print(f"Element Types: {types}")
    else:
        print("No BPMN model generated")

    print("\n💬 Explanation:")
    print("-" * 70)
    explanation = result.get("explanation")
    if explanation:
        print(explanation[:500] + ("..." if len(explanation) > 500 else ""))
    else:
        print("No explanation")

    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Modeler Agent - Generate BPMN 2.0 JSON from parsed process",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_modeler.py --parser my_process
  python run_modeler.py --input parser_output.txt --save my_bpmn
  python run_modeler.py --content "<pseudocode>...</pseudocode>"
        """,
    )
    parser.add_argument(
        "--parser",
        "-p",
        type=str,
        default=None,
        help="Parser output folder name (output/parser/[name]/)",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to input file with parsed pseudocode",
    )
    parser.add_argument(
        "--content", "-c", type=str, default=None, help="Direct pseudocode content"
    )
    parser.add_argument(
        "--save",
        "-s",
        type=str,
        default="bpmn_model",
        help="Output folder name in output/modeler/ (default: bpmn_model)",
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
        print("\n🚀 Initializing Modeler Agent...\n")
        modeler_agent = ModelerAgent()

        # Load input
        parser_folder = None
        if args.parser:
            parsed_pseudocode = load_parser_output(args.parser)
            parser_folder = args.parser
            print(f"📄 Input: Parser output from 'output/parser/{args.parser}/'")
        elif args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                parsed_pseudocode = f.read()
            print(f"📄 Input: {args.input}")
        elif args.content:
            parsed_pseudocode = args.content
            print(f"📄 Input: Direct content ({len(parsed_pseudocode)} chars)")
        else:
            print("❌ Error: Provide --parser, --input, or --content")
            return 1

        print("⏳ Generating BPMN 2.0 model...\n")

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
            if result.get("metadata"):
                print(
                    f"Metadata:\n{json.dumps(result['metadata'], indent=2, default=str)}"
                )
            print(f"\nRaw Response:\n{result.get('raw_response', 'N/A')[:1000]}")

        # Save results if not disabled
        if not args.no_save:
            print("\n💾 Saving results...")
            saved_files = modeler_agent.save_results(
                process_name=args.save, parser_folder=parser_folder
            )
            print(f"\n✅ Results saved to: output/modeler/{args.save}/")
            print("\nFiles saved:")
            for file_type, file_path in saved_files.items():
                print(f"  - {file_type}: {file_path.name}")
        else:
            print("\n⏭️  Skipping file save (--no-save flag)")

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
