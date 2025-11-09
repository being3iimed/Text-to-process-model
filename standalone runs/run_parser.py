#!/usr/bin/env python
"""
Standalone script to run the Parser Agent.

Converts natural language process descriptions to BPMN-style pseudocode.

Usage:
    python run_parser.py --input input/parser_output.txt
    python run_parser.py --content "your process description"
    python run_parser.py --input file.txt --save my_process
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.parser_agent import ParserAgent
from utils.file_handler import load_input_content


def print_results(result: dict) -> None:
    """Pretty print parser results."""
    print("\n" + "=" * 70)
    print("PARSER AGENT RESULTS")
    print("=" * 70)

    print(f"\n📊 Status: {result.get('status', 'unknown')}")

    print("\n📋 ELEMENTS:")
    print("-" * 70)
    elements = result.get("elements")
    if elements:
        print(elements)
    else:
        print("No elements extracted")

    print("\n💻 PSEUDOCODE:")
    print("-" * 70)
    pseudocode = result.get("pseudocode")
    if pseudocode:
        print(pseudocode)
    else:
        print("No pseudocode extracted")

    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parser Agent - Convert natural language to BPMN pseudocode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_parser.py --input input/parser_output.txt
  python run_parser.py --content "A customer places an order..."
  python run_parser.py --input file.txt --save my_process
        """,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to input file with process description",
    )
    parser.add_argument(
        "--content",
        "-c",
        type=str,
        default=None,
        help="Direct process description content",
    )
    parser.add_argument(
        "--save",
        "-s",
        type=str,
        default="parsed_process",
        help="Folder name to save results (default: parsed_process)",
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
        print("\n🚀 Initializing Parser Agent...\n")
        parser_agent = ParserAgent()

        # Load input
        if args.content:
            process_description = args.content
            print(f"📄 Input: Direct content ({len(process_description)} chars)")
        else:
            process_description = load_input_content(args.input)
            print(f"📄 Input: {args.input or 'input/parser_output.txt'}")

        print("⏳ Parsing process description...\n")

        # Run parser
        result = parser_agent.parse(process_description)

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
            saved_files = parser_agent.save_results(process_name=args.save)
            print(f"\n✅ Results saved to: output/parser/{args.save}/")
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
