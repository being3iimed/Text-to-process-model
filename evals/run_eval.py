import os
import pandas as pd
import networkx as nx
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
BASE_DIR = "."
GOLD_DIR = os.path.join(BASE_DIR, "bpmn_gold")
MISTRAL_LARGE_DIR = os.path.join(BASE_DIR, "mistral-large")
MISTRAL_MEDIUM_DIR = os.path.join(BASE_DIR, "mistral-medium")
OUTPUT_CSV = os.path.join(BASE_DIR, "bpmn_evaluation_results.csv")
OUTPUT_REPORT = os.path.join(BASE_DIR, "bpmn_evaluation_report.txt")


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


def normalize_node_type(node_type):
    """Normalize BPMN node types to abstract categories"""
    if 'Gateway' in node_type or 'gateway' in node_type:
        return 'gateway'
    elif 'Event' in node_type or 'event' in node_type:
        return 'event'
    elif 'Task' in node_type or 'task' in node_type:
        return 'task'
    else:
        return 'node'


def parse_bpmn(path):
    """Parse BPMN file and extract graph"""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        G = nx.DiGraph()
        
        # Get namespace
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'
        
        # Parse all elements
        for elem in root.iter():
            tag = elem.tag.replace(ns, '')
            
            # Add nodes
            if tag in ['task', 'serviceTask', 'userTask', 'manualTask', 'scriptTask', 
                       'businessRuleTask', 'sendTask', 'receiveTask',
                       'startEvent', 'endEvent', 
                       'exclusiveGateway', 'parallelGateway', 'inclusiveGateway', 
                       'eventBasedGateway', 'complexGateway',
                       'intermediateCatchEvent', 'intermediateThrowEvent', 
                       'boundaryEvent', 'subProcess', 'callActivity']:
                node_id = elem.get('id')
                if node_id:
                    G.add_node(node_id, type=normalize_node_type(tag), 
                              original_type=tag, name=elem.get('name', ''))
            
            # Add edges
            elif tag == 'sequenceFlow':
                source = elem.get('sourceRef')
                target = elem.get('targetRef')
                if source and target:
                    G.add_edge(source, target)
        
        return G if len(G.nodes) > 0 else None
    except:
        return None


def compute_semantic_metrics(path):
    """Extract semantic richness metrics from BPMN XML"""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        # Get namespace
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'
        
        metrics = {
            'task_count': 0,
            'event_count': 0,
            'gateway_count': 0,
            'gateway_types': set(),
            'named_elements': 0,
            'total_elements': 0,
            'task_types': set(),
            'event_types': set()
        }
        
        # Count all relevant elements
        for elem in root.iter():
            tag = elem.tag.replace(ns, '')
            
            # Task coverage
            if tag in ['task', 'serviceTask', 'userTask', 'manualTask', 'scriptTask', 
                       'businessRuleTask', 'sendTask', 'receiveTask']:
                metrics['task_count'] += 1
                metrics['task_types'].add(tag)
                metrics['total_elements'] += 1
                if elem.get('name'):
                    metrics['named_elements'] += 1
            
            # Event coverage
            elif tag in ['startEvent', 'endEvent', 'intermediateCatchEvent', 
                        'intermediateThrowEvent', 'boundaryEvent']:
                metrics['event_count'] += 1
                metrics['event_types'].add(tag)
                metrics['total_elements'] += 1
                if elem.get('name'):
                    metrics['named_elements'] += 1
            
            # Gateway diversity
            elif tag in ['exclusiveGateway', 'parallelGateway', 'inclusiveGateway', 
                        'eventBasedGateway', 'complexGateway']:
                metrics['gateway_count'] += 1
                metrics['gateway_types'].add(tag)
                metrics['total_elements'] += 1
                if elem.get('name'):
                    metrics['named_elements'] += 1
            
            # Also count subProcess and callActivity as task-like elements
            elif tag in ['subProcess', 'callActivity']:
                metrics['task_count'] += 1
                metrics['total_elements'] += 1
                if elem.get('name'):
                    metrics['named_elements'] += 1
        
        # Calculate ratios
        named_ratio = metrics['named_elements'] / metrics['total_elements'] if metrics['total_elements'] > 0 else 0
        
        return {
            'task_coverage': metrics['task_count'],
            'event_coverage': metrics['event_count'],
            'gateway_diversity': metrics['gateway_count'],
            'unique_gateway_types': len(metrics['gateway_types']),
            'unique_task_types': len(metrics['task_types']),
            'unique_event_types': len(metrics['event_types']),
            'named_elements_ratio': round(named_ratio, 3),
            'total_elements': metrics['total_elements']
        }
    except:
        return {
            'task_coverage': None,
            'event_coverage': None,
            'gateway_diversity': None,
            'unique_gateway_types': None,
            'unique_task_types': None,
            'unique_event_types': None,
            'named_elements_ratio': None,
            'total_elements': None
        }


def compute_metrics(G):
    """Compute graph metrics"""
    if G is None or len(G.nodes) == 0:
        return {'nodes': None, 'edges': None, 'density': None, 'cyclomatic': None}
    
    N = len(G.nodes)
    E = len(G.edges)
    P = nx.number_connected_components(G.to_undirected())
    
    return {
        'nodes': N,
        'edges': E,
        'density': round(E / (N * (N - 1)) if N > 1 else 0, 3),
        'cyclomatic': E - N + P
    }


def compare_graphs(G1, G2):
    """Compare two graphs structurally"""
    if G1 is None or G2 is None:
        return {'sim': 0.0}
    
    m1 = compute_metrics(G1)
    m2 = compute_metrics(G2)
    
    # Simple similarity based on nodes and edges
    node_sim = 1.0 - abs(m1['nodes'] - m2['nodes']) / max(m1['nodes'], m2['nodes']) if max(m1['nodes'], m2['nodes']) > 0 else 0.0
    edge_sim = 1.0 - abs(m1['edges'] - m2['edges']) / max(m1['edges'], m2['edges']) if max(m1['edges'], m2['edges']) > 0 else 0.0
    
    overall = (node_sim + edge_sim) / 2
    
    return {
        'node_sim': round(max(0, min(1, node_sim)), 3),
        'edge_sim': round(max(0, min(1, edge_sim)), 3),
        'overall_sim': round(max(0, min(1, overall)), 3)
    }


def compute_semantic_similarity(sem_gold, sem_gen):
    """Compute semantic similarity metrics between gold and generated"""
    if any(v is None for v in [sem_gold['task_coverage'], sem_gen['task_coverage']]):
        return {
            'task_coverage_similarity': None,
            'event_coverage_similarity': None,
            'gateway_diversity_similarity': None,
            'named_ratio_similarity': None,
            'semantic_richness_score': None
        }
    
    task_cov_sim = 1.0 - abs(sem_gold['task_coverage'] - sem_gen['task_coverage']) / max(sem_gold['task_coverage'], sem_gen['task_coverage']) if max(sem_gold['task_coverage'], sem_gen['task_coverage']) > 0 else 0.0
    event_cov_sim = 1.0 - abs(sem_gold['event_coverage'] - sem_gen['event_coverage']) / max(sem_gold['event_coverage'], sem_gen['event_coverage']) if max(sem_gold['event_coverage'], sem_gen['event_coverage']) > 0 else 0.0
    gateway_div_sim = 1.0 - abs(sem_gold['gateway_diversity'] - sem_gen['gateway_diversity']) / max(sem_gold['gateway_diversity'], sem_gen['gateway_diversity']) if max(sem_gold['gateway_diversity'], sem_gen['gateway_diversity']) > 0 else 0.0
    named_ratio_sim = 1.0 - abs(sem_gold['named_elements_ratio'] - sem_gen['named_elements_ratio'])
    
    semantic_richness = (task_cov_sim + event_cov_sim + gateway_div_sim + named_ratio_sim) / 4
    
    return {
        'task_coverage_similarity': round(max(0, min(1, task_cov_sim)), 3),
        'event_coverage_similarity': round(max(0, min(1, event_cov_sim)), 3),
        'gateway_diversity_similarity': round(max(0, min(1, gateway_div_sim)), 3),
        'named_ratio_similarity': round(max(0, min(1, named_ratio_sim)), 3),
        'semantic_richness_score': round(max(0, min(1, semantic_richness)), 3)
    }


def process_model(gold_path, gen_path, model_name, process_num):
    """Process a single model comparison"""
    # Parse both files
    G_gold = parse_bpmn(gold_path)
    G_gen = parse_bpmn(gen_path)
    
    if G_gold is None or G_gen is None:
        return None
    
    # Compute structural metrics
    m_gold = compute_metrics(G_gold)
    m_gen = compute_metrics(G_gen)
    comp = compare_graphs(G_gold, G_gen)
    
    # Compute semantic metrics
    sem_gold = compute_semantic_metrics(gold_path)
    sem_gen = compute_semantic_metrics(gen_path)
    
    # Calculate semantic richness comparison
    sem_sim = compute_semantic_similarity(sem_gold, sem_gen)
    
    return {
        'model': model_name,
        'process_num': process_num,
        # Structural metrics
        'gold_nodes': m_gold['nodes'],
        'gold_edges': m_gold['edges'],
        'gold_density': m_gold['density'],
        'gold_cyclomatic': m_gold['cyclomatic'],
        'gen_nodes': m_gen['nodes'],
        'gen_edges': m_gen['edges'],
        'gen_density': m_gen['density'],
        'gen_cyclomatic': m_gen['cyclomatic'],
        'node_similarity': comp['node_sim'],
        'edge_similarity': comp['edge_sim'],
        'structural_similarity': comp['overall_sim'],
        # Semantic metrics - Gold
        'gold_task_coverage': sem_gold['task_coverage'],
        'gold_event_coverage': sem_gold['event_coverage'],
        'gold_gateway_diversity': sem_gold['gateway_diversity'],
        'gold_unique_gateway_types': sem_gold['unique_gateway_types'],
        'gold_unique_task_types': sem_gold['unique_task_types'],
        'gold_unique_event_types': sem_gold['unique_event_types'],
        'gold_named_ratio': sem_gold['named_elements_ratio'],
        # Semantic metrics - Generated
        'gen_task_coverage': sem_gen['task_coverage'],
        'gen_event_coverage': sem_gen['event_coverage'],
        'gen_gateway_diversity': sem_gen['gateway_diversity'],
        'gen_unique_gateway_types': sem_gen['unique_gateway_types'],
        'gen_unique_task_types': sem_gen['unique_task_types'],
        'gen_unique_event_types': sem_gen['unique_event_types'],
        'gen_named_ratio': sem_gen['named_elements_ratio'],
        # Semantic similarity metrics
        'task_coverage_similarity': sem_sim['task_coverage_similarity'],
        'event_coverage_similarity': sem_sim['event_coverage_similarity'],
        'gateway_diversity_similarity': sem_sim['gateway_diversity_similarity'],
        'named_ratio_similarity': sem_sim['named_ratio_similarity'],
        'semantic_richness_score': sem_sim['semantic_richness_score']
    }


def get_matching_file(process_num, model_dir):
    """Find the matching file for a process number in a given directory"""
    files = os.listdir(model_dir)
    for f in files:
        if f.endswith('.bpmn'):
            # Extract number from filename (e.g., "process_01.bpmn" -> 1, "processes_01.bpmn" -> 1)
            num_str = f.split('_')[-1].replace('.bpmn', '')
            try:
                if int(num_str) == process_num:
                    return os.path.join(model_dir, f)
            except:
                pass
    return None


def main():
    # Initialize report writer
    report = ReportWriter(OUTPUT_REPORT)
    
    report.write("=" * 80)
    report.write("BPMN EVALUATION REPORT")
    report.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.write("=" * 80)
    
    report.write("\nCollecting files...")
    
    # Get all gold files
    gold_files = {}
    for f in sorted(os.listdir(GOLD_DIR)):
        if f.endswith('.bpmn'):
            num = int(f.replace('.bpmn', ''))
            gold_files[num] = os.path.join(GOLD_DIR, f)
    
    report.write(f"Found {len(gold_files)} gold BPMN files")
    
    results = []
    count = 0
    total = len(gold_files) * 2  # 2 models to evaluate
    
    # Process Mistral Large
    report.write(f"\n📊 Evaluating Mistral Large ({len(gold_files)} processes)...")
    for process_num in sorted(gold_files.keys()):
        count += 1
        report.write(f"[{count}/{total}] Processing process_{process_num:02d}...", end='')
        
        gold_path = gold_files[process_num]
        gen_path = get_matching_file(process_num, MISTRAL_LARGE_DIR)
        
        if not gen_path:
            report.write(" (generated file not found)")
            continue
        
        result = process_model(gold_path, gen_path, 'mistral-large', process_num)
        if result:
            results.append(result)
            report.write(" ✓")
        else:
            report.write(" (parse failed)")
    
    # Process Mistral Medium
    report.write(f"\n📊 Evaluating Mistral Medium ({len(gold_files)} processes)...")
    for process_num in sorted(gold_files.keys()):
        count += 1
        report.write(f"[{count}/{total}] Processing process_{process_num:02d}...", end='')
        
        gold_path = gold_files[process_num]
        gen_path = get_matching_file(process_num, MISTRAL_MEDIUM_DIR)
        
        if not gen_path:
            report.write(" (generated file not found)")
            continue
        
        result = process_model(gold_path, gen_path, 'mistral-medium', process_num)
        if result:
            results.append(result)
            report.write(" ✓")
        else:
            report.write(" (parse failed)")
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    
    report.write(f"\n✅ Complete! Evaluated {len(results)} model instances")
    report.write(f"Saved CSV to: {OUTPUT_CSV}\n")
    
    # Summary statistics by model
    report.write("=" * 80)
    report.write("SUMMARY BY MODEL")
    report.write("=" * 80)
    
    for model_name in ['mistral-large', 'mistral-medium']:
        model_df = df[df['model'] == model_name]
        if len(model_df) == 0:
            continue
            
        report.write(f"\n🔹 {model_name.upper()}")
        report.write("-" * 80)
        
        report.write(f"\nSTRUCTURAL METRICS:")
        report.write(f"  Avg nodes (gold): {model_df['gold_nodes'].mean():.1f}")
        report.write(f"  Avg nodes (gen): {model_df['gen_nodes'].mean():.1f}")
        report.write(f"  Avg node similarity: {model_df['node_similarity'].mean():.3f}")
        report.write(f"  Avg edge similarity: {model_df['edge_similarity'].mean():.3f}")
        report.write(f"  Avg structural similarity: {model_df['structural_similarity'].mean():.3f}")
        
        report.write(f"\nSEMANTIC RICHNESS METRICS:")
        report.write(f"  Avg task coverage (gold): {model_df['gold_task_coverage'].mean():.1f}")
        report.write(f"  Avg task coverage (gen): {model_df['gen_task_coverage'].mean():.1f}")
        report.write(f"  Avg event coverage (gold): {model_df['gold_event_coverage'].mean():.1f}")
        report.write(f"  Avg event coverage (gen): {model_df['gen_event_coverage'].mean():.1f}")
        report.write(f"  Avg gateway diversity (gold): {model_df['gold_gateway_diversity'].mean():.1f}")
        report.write(f"  Avg gateway diversity (gen): {model_df['gen_gateway_diversity'].mean():.1f}")
        report.write(f"  Avg named elements ratio (gold): {model_df['gold_named_ratio'].mean():.1%}")
        report.write(f"  Avg named elements ratio (gen): {model_df['gen_named_ratio'].mean():.1%}")
        
        report.write(f"\nSEMANTIC SIMILARITY SCORES:")
        report.write(f"  Task coverage similarity: {model_df['task_coverage_similarity'].mean():.3f}")
        report.write(f"  Event coverage similarity: {model_df['event_coverage_similarity'].mean():.3f}")
        report.write(f"  Gateway diversity similarity: {model_df['gateway_diversity_similarity'].mean():.3f}")
        report.write(f"  Named ratio similarity: {model_df['named_ratio_similarity'].mean():.3f}")
        report.write(f"  🎯 Semantic richness score: {model_df['semantic_richness_score'].mean():.3f}")
    
    report.write("\n" + "=" * 80)
    report.write("OVERALL COMPARISON")
    report.write("=" * 80)
    for metric in ['structural_similarity', 'semantic_richness_score']:
        report.write(f"\n{metric.replace('_', ' ').title()}:")
        for model_name in ['mistral-large', 'mistral-medium']:
            model_df = df[df['model'] == model_name]
            if len(model_df) > 0:
                report.write(f"  {model_name}: {model_df[metric].mean():.3f}")
    
    # Additional insights
    report.write("\n\n" + "=" * 80)
    report.write("DETAILED INSIGHTS & ANALYSIS")
    report.write("=" * 80)
    
    report.write("\n📊 QUALITY DISTRIBUTION")
    report.write("-" * 80)
    for model_name in ['mistral-large', 'mistral-medium']:
        model_df = df[df['model'] == model_name]
        excellent = len(model_df[model_df['semantic_richness_score'] > 0.80])
        good = len(model_df[(model_df['semantic_richness_score'] >= 0.70) & (model_df['semantic_richness_score'] <= 0.80)])
        fair = len(model_df[(model_df['semantic_richness_score'] >= 0.60) & (model_df['semantic_richness_score'] < 0.70)])
        moderate = len(model_df[(model_df['semantic_richness_score'] >= 0.50) & (model_df['semantic_richness_score'] < 0.60)])
        poor = len(model_df[model_df['semantic_richness_score'] < 0.50])
        
        report.write(f"\n{model_name}:")
        report.write(f"  Excellent (> 0.80): {excellent} processes ({excellent/len(model_df)*100:.1f}%)")
        report.write(f"  Good (0.70-0.80): {good} processes ({good/len(model_df)*100:.1f}%)")
        report.write(f"  Fair (0.60-0.70): {fair} processes ({fair/len(model_df)*100:.1f}%)")
        report.write(f"  Moderate (0.50-0.60): {moderate} processes ({moderate/len(model_df)*100:.1f}%)")
        report.write(f"  Poor (< 0.50): {poor} processes ({poor/len(model_df)*100:.1f}%)")
    
    report.write("\n\n🎯 LOWEST PERFORMING PROCESSES")
    report.write("-" * 80)
    lowest_5 = df.nsmallest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score', 'gateway_diversity_similarity']]
    for idx, row in lowest_5.iterrows():
        report.write(f"\nProcess {row['process_num']} ({row['model']}):")
        report.write(f"  Semantic Richness Score: {row['semantic_richness_score']:.3f}")
        report.write(f"  Gateway Diversity Similarity: {row['gateway_diversity_similarity']:.3f}")
    
    report.write("\n\n⭐ HIGHEST PERFORMING PROCESSES")
    report.write("-" * 80)
    highest_5 = df.nlargest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score', 'gateway_diversity_similarity']]
    for idx, row in highest_5.iterrows():
        report.write(f"\nProcess {row['process_num']} ({row['model']}):")
        report.write(f"  Semantic Richness Score: {row['semantic_richness_score']:.3f}")
        report.write(f"  Gateway Diversity Similarity: {row['gateway_diversity_similarity']:.3f}")
    
    report.write("\n\n⚠️  KEY FINDINGS")
    report.write("-" * 80)
    report.write("\n1. GATEWAY DIVERSITY CRISIS")
    report.write(f"   Gold avg gateways: {df['gold_gateway_diversity'].mean():.1f}")
    report.write(f"   Generated avg gateways: {df['gen_gateway_diversity'].mean():.1f}")
    report.write(f"   Loss: {(1 - df['gen_gateway_diversity'].mean() / df['gold_gateway_diversity'].mean()) * 100:.1f}%")
    report.write(f"   Avg similarity: {df['gateway_diversity_similarity'].mean():.3f}")
    
    report.write("\n2. EVENT OVER-GENERATION")
    report.write(f"   Gold avg events: {df['gold_event_coverage'].mean():.1f}")
    report.write(f"   Generated avg events: {df['gen_event_coverage'].mean():.1f}")
    report.write(f"   Increase: {((df['gen_event_coverage'].mean() / df['gold_event_coverage'].mean()) - 1) * 100:.1f}%")
    report.write(f"   Avg similarity: {df['event_coverage_similarity'].mean():.3f}")
    
    report.write("\n3. TASK COVERAGE (STRENGTH)")
    report.write(f"   Gold avg tasks: {df['gold_task_coverage'].mean():.1f}")
    report.write(f"   Generated avg tasks: {df['gen_task_coverage'].mean():.1f}")
    report.write(f"   Avg similarity: {df['task_coverage_similarity'].mean():.3f}")
    report.write(f"   Status: ✅ GOOD - Models capture tasks well")
    
    report.write("\n4. ELEMENT NAMING (STRENGTH)")
    report.write(f"   Gold avg named ratio: {df['gold_named_ratio'].mean():.1%}")
    report.write(f"   Generated avg named ratio: {df['gen_named_ratio'].mean():.1%}")
    report.write(f"   Status: ✅ EXCELLENT - Generated diagrams are well-documented")

    report.close()


if __name__ == "__main__":
    main()