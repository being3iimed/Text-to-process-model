"""Batch Orchestrator Agent - Process Multiple Processes from JSON."""

import argparse
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Paths
INPUT_DIR = Path(__file__).parent / "input"
PROCESSES_JSON_PATH = INPUT_DIR / "processes.json"
MAIN_SCRIPT = Path(__file__).parent / "main.py"
CONVERTER_SCRIPT = Path(__file__).parent / "single-converter.js"


def print_header():
    """Print batch processing header."""
    print("\n" + "=" * 80)
    print("BATCH ORCHESTRATOR AGENT - MULTI-PROCESS BPMN TRANSFORMER")
    print("=" * 80)
    print("Transform multiple process descriptions into BPMN 2.0 models")
    print("=" * 80 + "\n")


def load_processes_json() -> Dict[str, Dict[str, str]]:
    """
    Load processes from JSON file.

    Returns:
        Dictionary with categories and their processes
    """
    try:
        with open(PROCESSES_JSON_PATH, "r", encoding="utf-8") as f:
            processes = json.load(f)
        
        print(f"[OK] Loaded processes from: {PROCESSES_JSON_PATH}")
        
        # Count total processes
        total_count = sum(len(category_processes) for category_processes in processes.values())
        print(f"Found {len(processes)} categories with {total_count} total processes\n")
        
        return processes
    
    except FileNotFoundError:
        print(f"[ERROR] File not found: {PROCESSES_JSON_PATH}")
        print(f"   Please ensure the file exists at: {PROCESSES_JSON_PATH}\n")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON format: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error loading processes: {e}")
        return None


def flatten_processes(processes: Dict[str, Dict[str, str]]) -> List[Tuple[str, str, str]]:
    """
    Flatten nested process dictionary into list of tuples.

    Args:
        processes: Nested dictionary of categories and processes

    Returns:
        List of (category, process_name, process_description) tuples
    """
    flattened = []
    
    for category, category_processes in processes.items():
        for process_name, process_description in category_processes.items():
            # Create a clean process name: category_processname
            clean_name = f"{category}_{process_name}"
            flattened.append((category, clean_name, process_description))
    
    return flattened


def run_main_script(process_description: str, process_name: str, verbose: bool = False) -> bool:
    """
    Run the main.py orchestrator script for a single process.

    Args:
        process_description: The process description text
        process_name: Name for the process
        verbose: Whether to show detailed output

    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            sys.executable,  # Use same Python interpreter
            str(MAIN_SCRIPT),
            "--content", process_description,
            "--name", process_name
        ]
        
        if verbose:
            cmd.append("--verbose")
        
        print(f"   Running orchestrator...")
        
        # Set environment to handle UTF-8 properly on Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            env=env,
            encoding='utf-8',
            errors='replace'  # Replace problematic characters instead of crashing
        )
        
        if result.returncode == 0:
            print(f"   [OK] Orchestrator completed successfully")
            if verbose and result.stdout:
                print(f"\n--- Orchestrator Output ---")
                print(result.stdout)
                print(f"--- End Output ---\n")
            return True
        else:
            print(f"   [ERROR] Orchestrator failed with code {result.returncode}")
            print(f"\n--- Error Details ---")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            print(f"--- End Error Details ---\n")
            return False
    
    except Exception as e:
        print(f"   [ERROR] Error running orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_converter(process_name: str, verbose: bool = False) -> bool:
    """
    Run the Node.js converter script for a specific process.

    Args:
        process_name: Name of the process to convert
        verbose: Whether to show converter output

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        cmd = ["node", str(CONVERTER_SCRIPT), process_name]
        
        print(f"   Running BPMN converter...")
        
        # Set environment for UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            capture_output=not verbose, 
            text=True,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"   [OK] BPMN conversion completed successfully")
            return True
        else:
            print(f"   [ERROR] Converter failed with code {result.returncode}")
            if not verbose and result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    
    except FileNotFoundError:
        print(f"   [ERROR] Node.js or converter script not found")
        print(f"   Make sure Node.js is installed and {CONVERTER_SCRIPT} exists")
        return False
    except Exception as e:
        print(f"   [ERROR] Error running converter: {e}")
        return False


def process_batch(
    processes: List[Tuple[str, str, str]],
    convert_to_bpmn: bool = True,
    verbose: bool = False,
    stop_on_error: bool = False
):
    """
    Process multiple processes in batch mode.

    Args:
        processes: List of (category, process_name, process_description) tuples
        convert_to_bpmn: Whether to run converter after each orchestrator run
        verbose: Whether to show detailed output
        stop_on_error: Whether to stop on first error
    """
    total = len(processes)
    successful = 0
    failed = 0
    
    print(f"\nStarting batch processing of {total} processes...\n")
    print("=" * 80)
    
    for idx, (category, process_name, process_description) in enumerate(processes, 1):
        print(f"\n[{idx}/{total}] Processing: {process_name}")
        print(f"   Category: {category}")
        print(f"   Description length: {len(process_description)} chars")
        print("-" * 80)
        
        # Step 1: Run main.py orchestrator
        orchestrator_success = run_main_script(process_description, process_name, verbose)
        
        if not orchestrator_success:
            failed += 1
            print(f"   [FAILED] Failed at orchestrator stage")
            if stop_on_error:
                print(f"\n[WARNING] Stopping batch process due to error (stop_on_error=True)")
                break
            continue
        
        # Step 2: Run converter if requested
        if convert_to_bpmn:
            converter_success = run_converter(process_name, verbose)
            
            if not converter_success:
                failed += 1
                print(f"   [FAILED] Failed at conversion stage")
                if stop_on_error:
                    print(f"\n[WARNING] Stopping batch process due to error (stop_on_error=True)")
                    break
                continue
        
        successful += 1
        print(f"   [OK] Process completed successfully")
    
    # Print summary
    print("\n" + "=" * 80)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total processes: {total}")
    print(f"[OK] Successful: {successful}")
    print(f"[FAILED] Failed: {failed}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    print("=" * 80 + "\n")


def main():
    """Main entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Batch Orchestrator - Process multiple descriptions from JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_main.py                    # Process all from processes.json
  python batch_main.py --category retail  # Process only retail category
  python batch_main.py --no-convert       # Skip BPMN conversion
  python batch_main.py --verbose          # Show detailed output
  python batch_main.py --stop-on-error    # Stop at first error
        """,
    )
    
    parser.add_argument(
        "--category",
        "-c",
        type=str,
        default=None,
        help="Process only specific category (e.g., 'retail', 'finance')",
    )
    parser.add_argument(
        "--process",
        "-p",
        type=str,
        default=None,
        help="Process only specific process within category (e.g., 'checkout_process')",
    )
    parser.add_argument(
        "--no-convert",
        action="store_true",
        help="Skip BPMN XML conversion step",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output from orchestrator and converter",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop batch processing on first error",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available processes and exit",
    )

    args = parser.parse_args()

    try:
        print_header()
        
        # Load processes from JSON
        processes = load_processes_json()
        if processes is None:
            return 1
        
        # List mode
        if args.list:
            print("Available processes:\n")
            for category, category_processes in processes.items():
                print(f"  [{category}]:")
                for process_name in category_processes.keys():
                    print(f"     - {process_name}")
            print()
            return 0
        
        # Filter by category if specified
        if args.category:
            if args.category not in processes:
                print(f"[ERROR] Category '{args.category}' not found")
                print(f"Available categories: {', '.join(processes.keys())}\n")
                return 1
            processes = {args.category: processes[args.category]}
            print(f"Filtering to category: {args.category}\n")
        
        # Filter by specific process if specified
        if args.process:
            if not args.category:
                print(f"[ERROR] --process requires --category to be specified\n")
                return 1
            if args.process not in processes[args.category]:
                print(f"[ERROR] Process '{args.process}' not found in category '{args.category}'")
                print(f"Available processes: {', '.join(processes[args.category].keys())}\n")
                return 1
            processes = {args.category: {args.process: processes[args.category][args.process]}}
            print(f"Filtering to process: {args.process}\n")
        
        # Flatten processes
        flattened = flatten_processes(processes)
        
        if not flattened:
            print("[ERROR] No processes to process\n")
            return 1
        
        # Run batch processing
        process_batch(
            processes=flattened,
            convert_to_bpmn=not args.no_convert,
            verbose=args.verbose,
            stop_on_error=args.stop_on_error
        )
        
        return 0

    except KeyboardInterrupt:
        print("\n\n[WARNING] Batch processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {type(e).__name__}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())