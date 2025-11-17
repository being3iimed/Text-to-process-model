import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime

# Load the CSV
df = pd.read_csv('bpmn_evaluation_results.csv')

# Output file path
output_file = 'bpmn_validation_report.txt'

class ReportWriter:
    """Helper class to write to both file and console"""
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, 'w', encoding='utf-8')
    
    def write(self, text="", end="\n"):
        """Write to both file and console"""
        print(text, end=end)
        self.file.write(text + end)
        self.file.flush()
    
    def close(self):
        """Close the file"""
        self.file.close()


# Initialize report writer
report = ReportWriter(output_file)

report.write("\nBPMN EVALUATION RESULTS VALIDATION FRAMEWORK")
report.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.write("")

report.write("\n1. DATA INTEGRITY CHECKS")

# Check for missing values
missing_count = df.isnull().sum().sum()
report.write(f"\nMissing values: {missing_count} (should be 0)")
if missing_count > 0:
    report.write(f"  Found {missing_count} missing values:")
    report.write(str(df.isnull().sum()[df.isnull().sum() > 0]))

report.write("\n\n2. METRIC BOUNDS VALIDATION")

# All similarity scores should be 0.0 - 1.0
similarity_cols = [col for col in df.columns if 'similarity' in col or 'ratio' in col]
report.write(f"\nSimilarity scores (should be 0.0 - 1.0):")
for col in similarity_cols:
    min_val = df[col].min()
    max_val = df[col].max()
    out_of_bounds = ((df[col] < 0) | (df[col] > 1)).sum()
    status = "PASS" if (min_val >= 0 and max_val <= 1 and out_of_bounds == 0) else "FAIL"
    report.write(f"  {col}: [{min_val:.3f}, {max_val:.3f}] {status}")
    if out_of_bounds > 0:
        report.write(f"    Found {out_of_bounds} out-of-bounds values!")

# Node and edge counts should be positive
count_cols = ['gold_nodes', 'gold_edges', 'gen_nodes', 'gen_edges']
report.write(f"\nNode/Edge counts (should be > 0):")
for col in count_cols:
    negative = (df[col] <= 0).sum()
    status = "PASS" if negative == 0 else "FAIL"
    report.write(f"  {col}: min={df[col].min()}, max={df[col].max()} {status}")
    if negative > 0:
        report.write(f"    Found {negative} non-positive values!")

report.write("\n\n3. LOGICAL CONSISTENCY CHECKS")

# Check: density should be between 0 and 1
report.write(f"\nDensity values (should be 0.0 - 1.0):")
density_cols = ['gold_density', 'gen_density']
for col in density_cols:
    out_of_range = ((df[col] < 0) | (df[col] > 1)).sum()
    status = "PASS" if out_of_range == 0 else "FAIL"
    report.write(f"  {col}: min={df[col].min():.4f}, max={df[col].max():.4f} {status}")

# Check: cyclomatic complexity = edges - nodes + connected_components
report.write(f"\nCyclomatic complexity validation:")
for metric_type in ['gold', 'gen']:
    nodes = df[f'{metric_type}_nodes']
    edges = df[f'{metric_type}_edges']
    cyclomatic = df[f'{metric_type}_cyclomatic']
    
    # Cyclomatic should be >= 1 for connected graphs
    valid = (cyclomatic >= 0).sum()
    report.write(f"  {metric_type}: {valid}/55 have cyclomatic >= 0")
    
    # Cyclomatic should be <= edges
    valid = (cyclomatic <= edges).sum()
    status = "PASS" if valid == 55 else "FAIL"
    report.write(f"  {metric_type}: {valid}/55 have cyclomatic <= edges {status}")

# Check: similarity scores consistency
report.write(f"\nNode similarity vs node counts:")
issues_found = 0
for idx, row in df.iterrows():
    gold_nodes = row['gold_nodes']
    gen_nodes = row['gen_nodes']
    node_sim = row['node_similarity']
    
    # Calculate what similarity should theoretically be
    if gold_nodes > 0 and gen_nodes > 0:
        max_nodes = max(gold_nodes, gen_nodes)
        min_nodes = min(gold_nodes, gen_nodes)
        expected_min_sim = min_nodes / max_nodes
        
        if node_sim < expected_min_sim - 0.05:  # Allow small tolerance
            report.write(f"  Issue in Row {idx}: node_sim={node_sim:.3f}, but expected >= {expected_min_sim:.3f}")
            issues_found += 1

if issues_found == 0:
    report.write(f"  All {len(df)} rows have consistent node similarity")

report.write("\n\n4. METRIC CORRELATION CHECKS")

# semantic_richness_score should be average of 4 components
report.write(f"\nSemantic richness score = average of 4 components:")
component_cols = [
    'task_coverage_similarity',
    'event_coverage_similarity',
    'gateway_diversity_similarity',
    'named_ratio_similarity'
]

mismatches = 0
for idx, row in df.iterrows():
    calculated = np.mean([row[col] for col in component_cols])
    actual = row['semantic_richness_score']
    
    if abs(calculated - actual) > 0.001:  # Allow small rounding tolerance
        mismatches += 1
        if mismatches <= 3:
            report.write(f"  Row {idx}: calculated={calculated:.4f}, actual={actual:.4f}")

if mismatches == 0:
    report.write(f"  All {len(df)} rows have correct semantic richness scores")
else:
    report.write(f"  Found {mismatches} mismatches (may be rounding errors)")

# Check: structural_similarity = average of node and edge similarity
report.write(f"\nStructural similarity = average of node + edge similarity:")
mismatches = 0
for idx, row in df.iterrows():
    calculated = (row['node_similarity'] + row['edge_similarity']) / 2
    actual = row['structural_similarity']
    
    if abs(calculated - actual) > 0.001:
        mismatches += 1
        if mismatches <= 3:
            report.write(f"  Row {idx}: calculated={calculated:.4f}, actual={actual:.4f}")

if mismatches == 0:
    report.write(f"  All {len(df)} rows have correct structural similarity")
else:
    report.write(f"  Found {mismatches} mismatches")

report.write("\n\n5. DISTRIBUTION SANITY CHECKS")

report.write(f"\nSample sizes per model:")
for model in df['model'].unique():
    count = len(df[df['model'] == model])
    report.write(f"  {model}: {count} processes")

report.write(f"\nProcess number coverage:")
large_procs = set(df[df['model'] == 'mistral-large']['process_num'])
medium_procs = set(df[df['model'] == 'mistral-medium']['process_num'])
overlap = large_procs & medium_procs
report.write(f"  Mistral-large processes: {min(large_procs)}-{max(large_procs)} ({len(large_procs)} total)")
report.write(f"  Mistral-medium processes: {min(medium_procs)}-{max(medium_procs)} ({len(medium_procs)} total)")
report.write(f"  Overlap: {len(overlap)}/55")

report.write(f"\nDistribution of semantic richness scores:")
for model in ['mistral-large', 'mistral-medium']:
    model_df = df[df['model'] == model]
    scores = model_df['semantic_richness_score']
    report.write(f"  {model}:")
    report.write(f"    Mean: {scores.mean():.4f}")
    report.write(f"    Std:  {scores.std():.4f}")
    report.write(f"    Min:  {scores.min():.4f}")
    report.write(f"    Max:  {scores.max():.4f}")
    report.write(f"    Q25:  {scores.quantile(0.25):.4f}")
    report.write(f"    Q50:  {scores.quantile(0.50):.4f}")
    report.write(f"    Q75:  {scores.quantile(0.75):.4f}")

report.write("\n\n6. OUTLIER DETECTION")

# Find extreme cases
report.write(f"\nHighest semantic richness scores:")
top_5 = df.nlargest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score']]
report.write(top_5.to_string(index=False))

report.write(f"\n\nLowest semantic richness scores:")
bottom_5 = df.nsmallest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score']]
report.write(bottom_5.to_string(index=False))

# Find extreme node/edge mismatches
report.write(f"\n\nLargest node count discrepancies:")
df['node_diff'] = abs(df['gold_nodes'] - df['gen_nodes'])
top_node_diff = df.nlargest(3, 'node_diff')[['model', 'process_num', 'gold_nodes', 'gen_nodes', 'node_diff']]
report.write(top_node_diff.to_string(index=False))

# 7. COMPARE WITH GOLD STANDARD PATTERNS
report.write("\n\n7️⃣  COMPARE WITH GOLD STANDARD PATTERNS")
report.write("-" * 80)

report.write(f"\nGold standard statistics (across all processes):")
report.write(f"  Avg tasks per process: {df['gold_task_coverage'].mean():.1f}")
report.write(f"  Avg events per process: {df['gold_event_coverage'].mean():.1f}")
report.write(f"  Avg gateways per process: {df['gold_gateway_diversity'].mean():.1f}")
report.write(f"  Avg named ratio: {df['gold_named_ratio'].mean():.1%}")

report.write(f"\nGenerated statistics (Mistral-Large):")
large_df = df[df['model'] == 'mistral-large']
report.write(f"  Avg tasks per process: {large_df['gen_task_coverage'].mean():.1f}")
report.write(f"  Avg events per process: {large_df['gen_event_coverage'].mean():.1f}")
report.write(f"  Avg gateways per process: {large_df['gen_gateway_diversity'].mean():.1f}")
report.write(f"  Avg named ratio: {large_df['gen_named_ratio'].mean():.1%}")

report.write(f"\nGenerated statistics (Mistral-Medium):")
medium_df = df[df['model'] == 'mistral-medium']
report.write(f"  Avg tasks per process: {medium_df['gen_task_coverage'].mean():.1f}")
report.write(f"  Avg events per process: {medium_df['gen_event_coverage'].mean():.1f}")
report.write(f"  Avg gateways per process: {medium_df['gen_gateway_diversity'].mean():.1f}")
report.write(f"  Avg named ratio: {medium_df['gen_named_ratio'].mean():.1%}")

# 8. CROSS-VALIDATION: COMPARE SAME PROCESS ACROSS MODELS
report.write("\n\n8️⃣  CROSS-VALIDATION: SAME PROCESS ACROSS MODELS")
report.write("-" * 80)

report.write(f"\nFor the same gold processes, how different are model outputs?")
report.write(f"(Both models should produce different outputs for same gold input)")

comparison_stats = []
for process_num in df['process_num'].unique():
    gold_data = df[df['process_num'] == process_num].iloc[0]
    large_data = df[(df['process_num'] == process_num) & (df['model'] == 'mistral-large')].iloc[0]
    medium_data = df[(df['process_num'] == process_num) & (df['model'] == 'mistral-medium')].iloc[0]
    
    node_diff = abs(large_data['gen_nodes'] - medium_data['gen_nodes'])
    sem_rich_diff = abs(large_data['semantic_richness_score'] - medium_data['semantic_richness_score'])
    
    comparison_stats.append({
        'process': process_num,
        'node_diff': node_diff,
        'sem_rich_diff': sem_rich_diff
    })

comp_df = pd.DataFrame(comparison_stats)
report.write(f"\n  Average node difference between models: {comp_df['node_diff'].mean():.1f}")
report.write(f"  Average semantic richness difference: {comp_df['sem_rich_diff'].mean():.4f}")
report.write(f"  Processes where models produced identical output: {(comp_df['sem_rich_diff'] == 0).sum()}")

# 9. MANUAL SPOT CHECK (File-level validation)
report.write("\n\n9️⃣  FILE-LEVEL VALIDATION")
report.write("-" * 80)

bpmn_gold_dir = './bpmn_gold'
bpmn_large_dir = './mistral-large'
bpmn_medium_dir = './mistral-medium'

report.write(f"\nChecking if all referenced files exist:")

missing_files = {
    'gold-baseline': [],
    'mistral-large': [],
    'mistral-medium': []
}

for process_num in df['process_num'].unique():
    # Check gold files
    gold_file = os.path.join(bpmn_gold_dir, f'{process_num:02d}.bpmn')
    if not os.path.exists(gold_file):
        missing_files['gold'].append(process_num)
    
    # Check large files
    large_file = os.path.join(bpmn_large_dir, f'process_{process_num:02d}.bpmn')
    if not os.path.exists(large_file):
        missing_files['large'].append(process_num)
    
    # Check medium files
    medium_file = os.path.join(bpmn_medium_dir, f'processes_{process_num:02d}.bpmn')
    if not os.path.exists(medium_file):
        missing_files['medium'].append(process_num)

for dir_type, missing in missing_files.items():
    if missing:
        report.write(f"  Missing {dir_type} files: {missing}")
    else:
        report.write(f"  All {dir_type} files found")

report.close()