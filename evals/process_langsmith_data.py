import os
import json
from pathlib import Path
from typing import Any, Dict, Set, List
from dotenv import load_dotenv
from langsmith import Client
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = PROJECT_ROOT / "evals"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = EVALS_DIR / "langsmith_runs.json"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "text-to-process-model")

TARGET_DIRS = {
    "mistral-large-agents": "process_",
    "mistral-medium-agents": "processes_"
}

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

def load_json(file_path: Path) -> Any:
    """Load JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # print(f"Error reading {file_path}: {e}")
        return {}

def clean_run_id(local_id: str) -> str:
    """
    Clean local ID to match LangSmith ID.
    Example: 'lc_run--d0ee6af3...-0' -> 'd0ee6af3...'
    """
    if not local_id:
        return ""
    
    # Remove prefix
    if local_id.startswith("lc_run--"):
        local_id = local_id[8:]
    
    # Remove suffix (e.g., -0) if it exists and the rest is a UUID
    parts = local_id.split('-')
    # UUID has 5 parts (8-4-4-4-12). 
    # If we have > 5 parts, the extras are likely suffixes.
    if len(parts) > 5:
         return "-".join(parts[:5])
         
    return local_id

def fetch_all_runs() -> List[Dict[str, Any]]:
    """Fetch all runs from LangSmith."""
    print(f"Connecting to LangSmith project: {LANGSMITH_PROJECT}...")
    
    try:
        client = Client()
        runs = client.list_runs(
            project_name=LANGSMITH_PROJECT,
            execution_order=1, # Get root runs
            error=False,
        )
        
        runs_data = []
        print("Fetching runs from LangSmith API...")
        
        count = 0
        for run in runs:
            if hasattr(run, "dict"):
                run_dict = run.dict()
            elif hasattr(run, "model_dump"):
                run_dict = run.model_dump()
            else:
                run_dict = {
                    "id": str(run.id),
                    "name": run.name,
                    "run_type": run.run_type,
                    "start_time": run.start_time,
                    "end_time": run.end_time,
                    "extra": run.extra,
                    "inputs": run.inputs,
                    "outputs": run.outputs,
                    "error": run.error,
                }
            
            runs_data.append(run_dict)
            count += 1
            if count % 100 == 0:
                print(f"Fetched {count} runs...")
                
        print(f"Total runs fetched: {count}")
        return runs_data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def get_expected_runs() -> Dict[str, Dict[str, str]]:
    """
    Scan output directories and collect all expected run IDs with context.
    Returns: {cleaned_id: {agent, process, stage, raw_id}}
    """
    expected_runs = {}
    
    print(f"Scanning directories in {OUTPUT_DIR}...")
    
    for agent_group, folder_prefix in TARGET_DIRS.items():
        agent_dir = OUTPUT_DIR / agent_group
        if not agent_dir.exists():
            continue
            
        print(f"Processing {agent_group}...")
        
        # Scan parser runs
        parser_dir = agent_dir / "parser"
        if parser_dir.exists():
            for process_dir in parser_dir.iterdir():
                if not process_dir.is_dir() or not process_dir.name.startswith(folder_prefix):
                    continue
                
                meta_file = process_dir / "metadata.json"
                if meta_file.exists():
                    meta = load_json(meta_file)
                    if "parser_metadata" in meta and "id" in meta["parser_metadata"]:
                        raw_id = meta["parser_metadata"]["id"]
                        cleaned = clean_run_id(raw_id)
                        if cleaned:
                            expected_runs[cleaned] = {
                                "agent": agent_group,
                                "process": process_dir.name,
                                "stage": "parser",
                                "raw_id": raw_id
                            }

        # Scan modeler runs
        modeler_dir = agent_dir / "modeler"
        if modeler_dir.exists():
            for process_dir in modeler_dir.iterdir():
                if not process_dir.is_dir() or not process_dir.name.startswith(folder_prefix):
                    continue
                    
                meta_file = process_dir / "metadata.json"
                if meta_file.exists():
                    meta = load_json(meta_file)
                    if "modeler_metadata" in meta and "id" in meta["modeler_metadata"]:
                        raw_id = meta["modeler_metadata"]["id"]
                        cleaned = clean_run_id(raw_id)
                        if cleaned:
                            expected_runs[cleaned] = {
                                "agent": agent_group,
                                "process": process_dir.name,
                                "stage": "modeler",
                                "raw_id": raw_id
                            }
                            
    return expected_runs

def process_data():
    """Main processing function."""
    
    # 1. Fetch all runs
    all_runs = fetch_all_runs()
    if not all_runs:
        print("No runs fetched. Exiting.")
        return

    # 2. Get expected runs from local metadata
    expected_runs = get_expected_runs()
    print(f"Found {len(expected_runs)} expected runs from local metadata.")
    
    # 3. Filter runs and identify missing
    filtered_runs = []
    found_ids = set()
    
    print("Filtering runs...")
    
    for run in all_runs:
        run_id = str(run.get("id"))
        keep_run = False
        matched_id = None
        
        # Check main run ID
        if run_id in expected_runs:
            keep_run = True
            matched_id = run_id
        
        # Check message IDs if not already found
        if not keep_run:
            outputs = run.get("outputs", {})
            if outputs and isinstance(outputs, dict):
                messages = outputs.get("messages", [])
                if isinstance(messages, list):
                    for msg in messages:
                        if isinstance(msg, dict):
                            msg_id = msg.get("id")
                            if msg_id:
                                cleaned_id = clean_run_id(msg_id)
                                if cleaned_id and cleaned_id in expected_runs:
                                    keep_run = True
                                    matched_id = cleaned_id
                                    break
        
        if keep_run:
            # Inject metadata
            if matched_id and matched_id in expected_runs:
                info = expected_runs[matched_id]
                if "extra" not in run:
                    run["extra"] = {}
                if "metadata" not in run["extra"]:
                    run["extra"]["metadata"] = {}
                
                run["extra"]["metadata"]["agent"] = info["agent"]
                run["extra"]["metadata"]["process"] = info["process"]
                run["extra"]["metadata"]["stage"] = info["stage"]
                
            filtered_runs.append(run)
            if matched_id:
                found_ids.add(matched_id)

    # 4. Report Missing
    missing_count = 0
    print("\n" + "="*60)
    print("MISSING RUNS REPORT")
    print("="*60)
    
    for run_id, info in expected_runs.items():
        if run_id not in found_ids:
            missing_count += 1
            print(f"MISSING: [{info['agent']}] {info['process']} - {info['stage']}")
            print(f"  Expected ID: {run_id}")
            print(f"  Raw ID:      {info['raw_id']}")
            print("-" * 40)
            
    print("="*60)
    print(f"Total Expected: {len(expected_runs)}")
    print(f"Total Found:    {len(found_ids)}")
    print(f"Total Missing:  {missing_count}")
    print("="*60)
    
    # 5. Save filtered runs
    print(f"Saving {len(filtered_runs)} runs to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_runs, f, default=json_serial, indent=2)
    print("Done.")

if __name__ == "__main__":
    process_data()
