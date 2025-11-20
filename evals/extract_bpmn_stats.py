import os
import json
import csv
from pathlib import Path

# Configuration
BASE_DIR = Path("output")
AGENTS = ["mistral-large-agents", "mistral-medium-agents"]
MODELER_SUBDIR = "modeler"

def parse_bpmn_json(file_path):
    """Parses a BPMN JSON file and extracts element counts."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    metrics = {
        "Tasks": 0,
        "Events": 0,
        "Gateways": 0,
        "Exclusive Gateways": 0,
        "Parallel Gateways": 0,
        "Inclusive Gateways": 0,
        "Gateway Decisions": 0, # Exclusive + Inclusive
        "Gateway Types": set(),
        "Sequence Flows": 0,
        "Nodes": 0
    }

    # Navigate to flowElements
    # Structure: rootElements -> [0] -> flowElements
    root_elements = data.get("rootElements", [])
    if not root_elements:
        return metrics
    
    # Assuming the first root element is the Process
    process = root_elements[0]
    flow_elements = process.get("flowElements", [])

    for element in flow_elements:
        elem_type = element.get("$type", "")
        
        # Remove namespace prefix if present (e.g., "bpmn:")
        clean_type = elem_type.split(":")[-1] if ":" in elem_type else elem_type

        if clean_type == "SequenceFlow":
            metrics["Sequence Flows"] += 1
            continue

        # Count Nodes (Tasks, Events, Gateways)
        is_node = False

        if "Task" in clean_type:
            metrics["Tasks"] += 1
            is_node = True
        elif "Event" in clean_type:
            metrics["Events"] += 1
            is_node = True
        elif "Gateway" in clean_type:
            metrics["Gateways"] += 1
            metrics["Gateway Types"].add(clean_type)
            is_node = True
            
            if clean_type == "ExclusiveGateway":
                metrics["Exclusive Gateways"] += 1
            elif clean_type == "ParallelGateway":
                metrics["Parallel Gateways"] += 1
            elif clean_type == "InclusiveGateway":
                metrics["Inclusive Gateways"] += 1

        if is_node:
            metrics["Nodes"] += 1

    metrics["Gateway Decisions"] = metrics["Exclusive Gateways"] + metrics["Inclusive Gateways"]
    metrics["Gateway Types Count"] = len(metrics["Gateway Types"])
    
    return metrics

def process_agent_directory(agent_dir_name):
    """Processes all process folders for a given agent directory."""
    agent_dir = BASE_DIR / agent_dir_name / MODELER_SUBDIR
    results = []

    if not agent_dir.exists():
        print(f"Directory not found: {agent_dir}")
        return results

    # Simplify model name: remove "-agents" suffix
    model_name = agent_dir_name.replace("-agents", "")

    # Iterate over process folders (e.g., process_01, process_02)
    # Sort to ensure order
    for process_folder in sorted(agent_dir.iterdir()):
        if process_folder.is_dir() and (process_folder.name.startswith("process_") or process_folder.name.startswith("processes_")):
            json_file = process_folder / "bpmn_model.json"
            if json_file.exists():
                metrics = parse_bpmn_json(json_file)
                if metrics:
                    metrics["PMR"] = process_folder.name
                    metrics["Model"] = model_name
                    results.append(metrics)

    return results

def save_csvs_and_means(all_data):
    """Saves individual CSVs and a combined mean comparison CSV using standard library."""
    
    if not all_data:
        print("No data found.")
        return

    evals_dir = Path("evals")
    evals_dir.mkdir(exist_ok=True)

    # Columns to include in the output
    output_columns = [
        "PMR", "Model", "Nodes", "Tasks", "Events", "Gateways", 
        "Exclusive Gateways", "Parallel Gateways", "Inclusive Gateways",
        "Gateway Decisions", "Gateway Types Count", "Sequence Flows"
    ]
    
    # Numeric columns for mean calculation
    numeric_cols = [
        "Nodes", "Tasks", "Events", "Gateways", 
        "Exclusive Gateways", "Parallel Gateways", "Inclusive Gateways",
        "Gateway Decisions", "Gateway Types Count", "Sequence Flows"
    ]

    means_data = {}
    models = set()

    # Group data by Model
    model_groups = {}
    for row in all_data:
        model = row["Model"]
        models.add(model)
        if model not in model_groups:
            model_groups[model] = []
        model_groups[model].append(row)

    sorted_models = sorted(list(models))

    for model in sorted_models:
        model_rows = model_groups[model]
        
        # Save individual CSV
        # Filename still uses the original agent directory name convention for clarity or simplified?
        # User said "generated mistral-large-agents_stats.csv", so let's keep the filename as is or close to it.
        # But since we don't have the directory name here easily without passing it, 
        # let's use the model name + "_agents_stats.csv" to match previous pattern if desired, 
        # OR just model_name + "_stats.csv". 
        # The user prompt mentioned "mistral-large-agents_stats.csv", so I will reconstruct that name.
        filename = f"{model}-agents_stats.csv"
        output_file = evals_dir / filename
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=output_columns, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(model_rows)
            print(f"Saved raw stats to: {output_file}")
        except Exception as e:
            print(f"Error saving {output_file}: {e}")

        # Calculate Means
        model_means = {}
        count = len(model_rows)
        if count > 0:
            for col in numeric_cols:
                total = sum(row.get(col, 0) for row in model_rows)
                model_means[col] = total / count
            means_data[model] = model_means

    # Create Comparison CSV (Row-wise)
    if means_data:
        comparison_file = evals_dir / "bpmn_stats_mean_comparison.csv"
        try:
            with open(comparison_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header: Model, Metric1, Metric2...
                header = ["Model"] + numeric_cols
                writer.writerow(header)
                
                for model in sorted_models:
                    row = [model]
                    for col in numeric_cols:
                        val = means_data.get(model, {}).get(col, "")
                        row.append(f"{val:.2f}" if isinstance(val, (int, float)) else val)
                    writer.writerow(row)
            
            print(f"Saved mean comparison to: {comparison_file}")
            
            # Print for verification
            print("\nMean Comparison:")
            # Calculate column widths for pretty printing
            col_widths = [max(len(col), 10) for col in header]
            
            # Print Header
            header_str = " | ".join(h.ljust(w) for h, w in zip(header, col_widths))
            print(header_str)
            print("-" * len(header_str))
            
            # Print Rows
            for model in sorted_models:
                row_vals = [model] + [f"{means_data.get(model, {}).get(col, 0):.2f}" for col in numeric_cols]
                row_str = " | ".join(val.ljust(w) for val, w in zip(row_vals, col_widths))
                print(row_str)

        except Exception as e:
            print(f"Error saving comparison CSV: {e}")

def main():
    all_results = []
    for agent_dir in AGENTS:
        print(f"Processing {agent_dir}...")
        results = process_agent_directory(agent_dir)
        all_results.extend(results)
    
    save_csvs_and_means(all_results)

if __name__ == "__main__":
    main()
