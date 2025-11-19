"""
Performance Aggregator

Aggregates performance metrics (latency, token usage) from `langsmith_runs.json`.
Requires `langsmith_runs.json` to be enriched with metadata (agent, process, stage).
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = PROJECT_ROOT / "evals"
LANGSMITH_RUNS_FILE = EVALS_DIR / "langsmith_runs.json"

def load_json(file_path: Path) -> Any:
    """Load JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def aggregate_metrics():
    """Aggregate metrics from enriched LangSmith runs."""
    
    print(f"Loading runs from {LANGSMITH_RUNS_FILE}...")
    runs = load_json(LANGSMITH_RUNS_FILE)
    
    if not runs:
        print("No runs found.")
        return

    data = []
    
    for run in runs:
        # Extract metadata
        extra = run.get("extra", {})
        metadata = extra.get("metadata", {})
        
        agent = metadata.get("agent")
        process = metadata.get("process")
        stage = metadata.get("stage")
        
        if not (agent and process and stage):
            # Skip runs without injected metadata
            continue
            
        # Extract Metrics
        start_time = run.get("start_time")
        end_time = run.get("end_time")
        
        latency = 0.0
        if start_time and end_time:
            try:
                start = pd.to_datetime(start_time)
                end = pd.to_datetime(end_time)
                latency = (end - start).total_seconds()
            except Exception:
                pass
                
        total_tokens = run.get("total_tokens", 0)
        prompt_tokens = run.get("prompt_tokens", 0)
        completion_tokens = run.get("completion_tokens", 0)
        
        # Check for valid output (proxy for success)
        outputs = run.get("outputs", {})
        success = False
        if outputs:
             success = True

        data.append({
            "Agent": agent,
            "Process": process,
            "Stage": stage,
            "Latency": latency,
            "Tokens": total_tokens,
            "Prompt_Tokens": prompt_tokens,
            "Completion_Tokens": completion_tokens,
            "Success": success
        })

    if not data:
        print("No enriched runs found in data. run process_langsmith_data.py")
        return

    df = pd.DataFrame(data)
    
    # Prepare output capturing
    output_buffer = []
    def log(msg=""):
        print(msg)
        output_buffer.append(str(msg))

    # Group by Agent
    log("\n" + "="*80)
    log("PERFORMANCE METRICS SUMMARY")
    log("="*80)
    
    for agent, group in df.groupby("Agent"):
        log(f"\nAgent: {agent}")
        log("-" * 40)
        
        # Total Execution Time (Sum of Parser + Modeler for each process)
        # We need to pivot to get Parser and Modeler times for each process
        pivot_df = group.pivot_table(
            index="Process", 
            columns="Stage", 
            values=["Latency", "Tokens", "Prompt_Tokens", "Completion_Tokens"], 
            aggfunc="sum"
        )
        
        # Flatten columns
        pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
        
        # Calculate Total Time and Tokens per process
        if "Latency_parser" in pivot_df.columns and "Latency_modeler" in pivot_df.columns:
            pivot_df["Total_Time"] = pivot_df["Latency_parser"].fillna(0) + pivot_df["Latency_modeler"].fillna(0)
        else:
             pivot_df["Total_Time"] = pivot_df.get("Latency_parser", 0) + pivot_df.get("Latency_modeler", 0)

        # Helper to sum parser + modeler for a metric
        def sum_stages(metric_base):
            p = pivot_df.get(f"{metric_base}_parser", 0).fillna(0)
            m = pivot_df.get(f"{metric_base}_modeler", 0).fillna(0)
            return p + m

        pivot_df["Total_Tokens"] = sum_stages("Tokens")
        pivot_df["Total_Prompt_Tokens"] = sum_stages("Prompt_Tokens")
        pivot_df["Total_Completion_Tokens"] = sum_stages("Completion_Tokens")

        # Metrics to report
        stats = {
            "Total Execution Time (s)": pivot_df["Total_Time"],
            "Parser Time (s)": pivot_df.get("Latency_parser", pd.Series()),
            "Modeler Time (s)": pivot_df.get("Latency_modeler", pd.Series()),
            "Total Tokens": pivot_df["Total_Tokens"],
            "Total Prompt Tokens": pivot_df["Total_Prompt_Tokens"],
            "Total Completion Tokens": pivot_df["Total_Completion_Tokens"]
        }
        
        results = []
        for metric_name, series in stats.items():
            if series.empty:
                continue
            results.append({
                "Metric": metric_name,
                "Mean": series.mean(),
                "Range": f"{series.min():.2f} - {series.max():.2f}",
                "Median": series.median(),
                "Std Dev": series.std()
            })
            
        res_df = pd.DataFrame(results)
        log(res_df.to_string(index=False, float_format=lambda x: "{:.2f}".format(x)))
        log("-" * 80)

    # Save to file
    report_path = EVALS_DIR / "performance_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_buffer))
    print(f"\nReport saved to {report_path}")

if __name__ == "__main__":
    aggregate_metrics()
