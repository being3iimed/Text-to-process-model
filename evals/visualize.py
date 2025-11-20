import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load results
df = pd.read_csv('evals/bpmn_evaluation_results.csv')

# Create output directory if it doesn't exist
VIS_DIR = 'evals/visualizations'
os.makedirs(VIS_DIR, exist_ok=True)

# ============ VISUALIZATION 1: Semantic Dimension Comparison ============
fig1, ax1 = plt.subplots(figsize=(10, 6))
dimensions = ['Task\nCoverage', 'Event\nCoverage', 'Gateway\nDiversity', 'Named\nRatio']
scores = [
    df['task_coverage_similarity'].mean(),
    df['event_coverage_similarity'].mean(),
    df['gateway_diversity_similarity'].mean(),
    df['named_ratio_similarity'].mean()
]
colors = ['#2ecc71' if s > 0.7 else '#f39c12' if s > 0.5 else '#e74c3c' for s in scores]
bars = ax1.bar(dimensions, scores, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
ax1.axhline(y=0.654, color='blue', linestyle='--', linewidth=2, label=f'Avg Richness: 0.654')
ax1.set_ylabel('Similarity Score', fontsize=12, fontweight='bold')
ax1.set_title('Semantic Richness by Dimension', fontsize=14, fontweight='bold')
ax1.set_ylim(0, 1.0)
ax1.legend(fontsize=11)
ax1.grid(axis='y', alpha=0.3)
for bar, score in zip(bars, scores):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
            f'{score:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.tight_layout()
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load results
df = pd.read_csv('evals/bpmn_evaluation_results.csv')

# Create output directory if it doesn't exist
VIS_DIR = 'evals/visualizations'
os.makedirs(VIS_DIR, exist_ok=True)

# ============ VISUALIZATION 1: Semantic Dimension Comparison ============
fig1, ax1 = plt.subplots(figsize=(10, 6))
dimensions = ['Task\nCoverage', 'Event\nCoverage', 'Gateway\nDiversity', 'Named\nRatio']
scores = [
    df['task_coverage_similarity'].mean(),
    df['event_coverage_similarity'].mean(),
    df['gateway_diversity_similarity'].mean(),
    df['named_ratio_similarity'].mean()
]
colors = ['#2ecc71' if s > 0.7 else '#f39c12' if s > 0.5 else '#e74c3c' for s in scores]
bars = ax1.bar(dimensions, scores, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
ax1.axhline(y=0.654, color='blue', linestyle='--', linewidth=2, label=f'Avg Richness: 0.654')
ax1.set_ylabel('Similarity Score', fontsize=12, fontweight='bold')
ax1.set_title('Semantic Richness by Dimension', fontsize=14, fontweight='bold')
ax1.set_ylim(0, 1.0)
ax1.legend(fontsize=11)
ax1.grid(axis='y', alpha=0.3)
for bar, score in zip(bars, scores):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
            f'{score:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/01_semantic_dimensions.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/01_semantic_dimensions.png")
plt.close()

# ============ VISUALIZATION 2: Distribution of Semantic Richness ============
fig2, ax2 = plt.subplots(figsize=(10, 6))
ax2.hist(df['semantic_richness_score'], bins=15, color='#3498db', alpha=0.7, edgecolor='black', linewidth=1.5)
ax2.axvline(df['semantic_richness_score'].mean(), color='red', linestyle='--', 
           linewidth=2.5, label=f'Mean: {df["semantic_richness_score"].mean():.3f}')
ax2.axvline(df['semantic_richness_score'].median(), color='green', linestyle='--', 
           linewidth=2.5, label=f'Median: {df["semantic_richness_score"].median():.3f}')
ax2.set_xlabel('Semantic Richness Score', fontsize=12, fontweight='bold')
ax2.set_ylabel('Number of Models', fontsize=12, fontweight='bold')
ax2.set_title('Distribution of Semantic Richness & Similarity Scores', fontsize=14, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/02_richness_distribution.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/02_richness_distribution.png")
plt.close()

# ============ VISUALIZATION 3: Structural vs Semantic Similarity ============
fig3, ax3 = plt.subplots(figsize=(10, 8))
scatter = ax3.scatter(df['structural_similarity'], df['semantic_richness_score'], 
                     c=df['gateway_diversity_similarity'], cmap='RdYlGn', 
                     s=120, alpha=0.6, edgecolor='black', linewidth=1.5)
ax3.set_xlabel('Structural Similarity', fontsize=12, fontweight='bold')
ax3.set_ylabel('Semantic Richness Score', fontsize=12, fontweight='bold')
ax3.set_title('Structural vs Semantic Quality', fontsize=14, fontweight='bold')
ax3.set_xlim(0.2, 1.0)
ax3.set_ylim(0.4, 0.9)
cbar = plt.colorbar(scatter, ax=ax3)
cbar.set_label('Gateway Diversity Similarity', fontsize=11, fontweight='bold')
ax3.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/03_structural_vs_semantic.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/03_structural_vs_semantic.png")
plt.close()

# ============ VISUALIZATION 4: Node/Edge Coverage ============
fig4, ax4 = plt.subplots(figsize=(10, 6))
categories = ['Tasks', 'Events', 'Gateways']
gold_counts = [
    df['gold_task_coverage'].mean(),
    df['gold_event_coverage'].mean(),
    df['gold_gateway_diversity'].mean()
]
gen_counts = [
    df['gen_task_coverage'].mean(),
    df['gen_event_coverage'].mean(),
    df['gen_gateway_diversity'].mean()
]
x = np.arange(len(categories))
width = 0.35
bars1 = ax4.bar(x - width/2, gold_counts, width, label='Gold Standard', color='#3498db', alpha=0.7, edgecolor='black', linewidth=1.5)
bars2 = ax4.bar(x + width/2, gen_counts, width, label='Generated Models', color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=1.5)
ax4.set_ylabel('Average Count', fontsize=12, fontweight='bold')
ax4.set_title('Feature Count: Gold vs Generated', fontsize=14, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(categories, fontsize=11)
ax4.legend(fontsize=11)
ax4.grid(axis='y', alpha=0.3)
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{height:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/04_feature_count_comparison.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/04_feature_count_comparison.png")
plt.close()

# ============ VISUALIZATION 5: Top & Bottom Performers ============
fig5, ax5 = plt.subplots(figsize=(10, 8))
top5 = df.nlargest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score']].reset_index(drop=True)
bottom5 = df.nsmallest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score']].reset_index(drop=True)
top5['label'] = 'Process ' + top5['process_num'].astype(str) + '\n(' + top5['model'].str.replace('mistral-', '') + ')'
bottom5['label'] = 'Process ' + bottom5['process_num'].astype(str) + '\n(' + bottom5['model'].str.replace('mistral-', '') + ')'
combined = pd.concat([top5, bottom5], ignore_index=True)
colors_perf = ['#2ecc71']*5 + ['#e74c3c']*5
bars = ax5.barh(range(len(combined)), combined['semantic_richness_score'], color=colors_perf, alpha=0.7, edgecolor='black', linewidth=1.5)
ax5.set_yticks(range(len(combined)))
ax5.set_yticklabels(combined['label'], fontsize=10)
ax5.set_xlabel('Semantic Richness Score', fontsize=12, fontweight='bold')
ax5.set_title('Top 5 & Bottom 5 Performers', fontsize=14, fontweight='bold')
ax5.set_xlim(0, 1.0)
ax5.grid(axis='x', alpha=0.3)
for i, (bar, val) in enumerate(zip(bars, combined['semantic_richness_score'])):
    ax5.text(val + 0.02, i, f'{val:.3f}', va='center', fontweight='bold', fontsize=10)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/05_top_bottom_performers.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/05_top_bottom_performers.png")
plt.close()

# ============ VISUALIZATION 6: Documentation & Named Elements ============
fig6, ax6 = plt.subplots(figsize=(10, 6))
named_data = [
    df['gold_named_ratio'].mean(),
    df['gen_named_ratio'].mean()
]
labels = ['Gold Models', 'Generated Models']
colors_named = ['#3498db', '#2ecc71']
bars = ax6.bar(labels, named_data, color=colors_named, alpha=0.7, edgecolor='black', linewidth=2)
ax6.set_ylabel('Named Elements Ratio', fontsize=12, fontweight='bold')
ax6.set_title('Documentation Quality (Named Elements)', fontsize=14, fontweight='bold')
ax6.set_ylim(0, 1.0)
ax6.grid(axis='y', alpha=0.3)
for bar, val in zip(bars, named_data):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height + 0.02,
            f'{val:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=12)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/06_documentation_quality.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/06_documentation_quality.png")
plt.close()

# ============ VISUALIZATION 7: Model Comparison (Mistral-Large vs Medium) ============
fig7, ax7 = plt.subplots(figsize=(10, 6))
models = ['Mistral-Large', 'Mistral-Medium']
metrics_to_compare = [
    ('Task Coverage', 'task_coverage_similarity'),
    ('Event Coverage', 'event_coverage_similarity'),
    ('Gateway Diversity', 'gateway_diversity_similarity'),
    ('Named Ratio', 'named_ratio_similarity'),
    ('Semantic Richness', 'semantic_richness_score')
]
large_scores = [df[df['model'] == 'mistral-large'][metric].mean() for _, metric in metrics_to_compare]
medium_scores = [df[df['model'] == 'mistral-medium'][metric].mean() for _, metric in metrics_to_compare]
metric_labels = [label for label, _ in metrics_to_compare]
x = np.arange(len(metric_labels))
width = 0.35
bars1 = ax7.bar(x - width/2, large_scores, width, label='Mistral-Large', color='#3498db', alpha=0.7, edgecolor='black', linewidth=1.5)
bars2 = ax7.bar(x + width/2, medium_scores, width, label='Mistral-Medium', color='#e67e22', alpha=0.7, edgecolor='black', linewidth=1.5)
ax7.set_ylabel('Score', fontsize=12, fontweight='bold')
ax7.set_title('Model Comparison: Mistral-Large vs Mistral-Medium', fontsize=14, fontweight='bold')
ax7.set_xticks(x)
ax7.set_xticklabels(metric_labels, fontsize=10)
ax7.legend(fontsize=11)
ax7.set_ylim(0, 1.0)
ax7.grid(axis='y', alpha=0.3)
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/07_model_comparison.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/07_model_comparison.png")
plt.close()

# ============ VISUALIZATION 8: Gateway Loss Analysis ============
fig8, ax8 = plt.subplots(figsize=(10, 6))
gateway_diff = df['gold_gateway_diversity'] - df['gen_gateway_diversity']
ax8.hist(gateway_diff, bins=20, color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=1.5)
ax8.axvline(gateway_diff.mean(), color='darkred', linestyle='--', linewidth=2.5, 
           label=f'Average Loss: {gateway_diff.mean():.2f} gateways')
ax8.set_xlabel('Gateway Count Difference (Gold - Generated)', fontsize=12, fontweight='bold')
ax8.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax8.set_title('Gateway Loss Analysis (How Many Gateways Were Lost)', fontsize=14, fontweight='bold')
ax8.legend(fontsize=11)
ax8.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/08_gateway_loss_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/08_gateway_loss_analysis.png")
plt.close()

# ============ VISUALIZATION 9: Quality Score Distribution by Category ============
fig9, ax9 = plt.subplots(figsize=(12, 6))
quality_bins = [0, 0.5, 0.6, 0.7, 0.8, 1.0]
quality_labels = ['Poor\n(<0.50)', 'Moderate\n(0.50-0.60)', 'Fair\n(0.60-0.70)', 'Good\n(0.70-0.80)', 'Excellent\n(>0.80)']
hist_data, _ = np.histogram(df['semantic_richness_score'], bins=quality_bins)
colors_quality = ['#e74c3c', '#f39c12', '#f1c40f', '#3498db', '#2ecc71']
bars = ax9.bar(quality_labels, hist_data, color=colors_quality, alpha=0.7, edgecolor='black', linewidth=1.5)
ax9.set_ylabel('Number of Models', fontsize=12, fontweight='bold')
ax9.set_title('Model Quality Distribution', fontsize=14, fontweight='bold')
ax9.grid(axis='y', alpha=0.3)
for bar, count in zip(bars, hist_data):
    height = bar.get_height()
    ax9.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{int(count)}', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/09_quality_distribution.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/09_quality_distribution.png")
plt.close()

# ============ VISUALIZATION 10: Correlation Heatmap ============
fig10, ax10 = plt.subplots(figsize=(10, 8))
correlation_cols = ['task_coverage_similarity', 'event_coverage_similarity', 
                    'gateway_diversity_similarity', 'named_ratio_similarity', 
                    'semantic_richness_score', 'structural_similarity']
correlation_matrix = df[correlation_cols].corr()
im = ax10.imshow(correlation_matrix, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')
ax10.set_xticks(range(len(correlation_cols)))
ax10.set_yticks(range(len(correlation_cols)))
ax10.set_xticklabels(['Task', 'Event', 'Gateway', 'Named', 'Richness', 'Structural'], fontsize=10, rotation=45, ha='right')
ax10.set_yticklabels(['Task', 'Event', 'Gateway', 'Named', 'Richness', 'Structural'], fontsize=10)
ax10.set_title('Metric Correlation Heatmap', fontsize=14, fontweight='bold')
for i in range(len(correlation_cols)):
    for j in range(len(correlation_cols)):
        text = ax10.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                        ha="center", va="center", color="black", fontweight='bold', fontsize=10)
cbar = plt.colorbar(im, ax=ax10)
cbar.set_label('Correlation', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{VIS_DIR}/10_correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {VIS_DIR}/10_correlation_heatmap.png")
plt.close()

# ============ Generate Summary Statistics ============
print("\n" + "="*80)
print("SEMANTIC RICHNESS ANALYSIS SUMMARY")
print("="*80)

print(f"\nOVERALL SCORES")
print(f"  Structural Similarity: {df['structural_similarity'].mean():.3f} ± {df['structural_similarity'].std():.3f}")
print(f"  Semantic Richness: {df['semantic_richness_score'].mean():.3f} ± {df['semantic_richness_score'].std():.3f}")

print(f"\nDIMENSION BREAKDOWN")
print(f"  Task Coverage Similarity: {df['task_coverage_similarity'].mean():.3f}")
print(f"  Event Coverage Similarity: {df['event_coverage_similarity'].mean():.3f}")
print(f"  Gateway Diversity Similarity: {df['gateway_diversity_similarity'].mean():.3f} [CRITICAL ISSUE]")
print(f"  Named Ratio Similarity: {df['named_ratio_similarity'].mean():.3f}")

print(f"\nFEATURE COUNTS")
print(f"  Gold Tasks: {df['gold_task_coverage'].mean():.1f} | Gen Tasks: {df['gen_task_coverage'].mean():.1f}")
print(f"  Gold Events: {df['gold_event_coverage'].mean():.1f} | Gen Events: {df['gen_event_coverage'].mean():.1f}")
print(f"  Gold Gateways: {df['gold_gateway_diversity'].mean():.1f} | Gen Gateways: {df['gen_gateway_diversity'].mean():.1f}")
print(f"  Gold Named Ratio: {df['gold_named_ratio'].mean():.1%} | Gen Named Ratio: {df['gen_named_ratio'].mean():.1%}")

print(f"\nTOP 5 MODELS")
top5_models = df.nlargest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score', 'gateway_diversity_similarity']]
for idx, (i, row) in enumerate(top5_models.iterrows(), 1):
    print(f"  {idx}. Process {row['process_num']} ({row['model']}): {row['semantic_richness_score']:.3f} (Gateway: {row['gateway_diversity_similarity']:.3f})")

print(f"\nBOTTOM 5 MODELS")
bottom5_models = df.nsmallest(5, 'semantic_richness_score')[['model', 'process_num', 'semantic_richness_score', 'gateway_diversity_similarity']]
for idx, (i, row) in enumerate(bottom5_models.iterrows(), 1):
    print(f"  {idx}. Process {row['process_num']} ({row['model']}): {row['semantic_richness_score']:.3f} (Gateway: {row['gateway_diversity_similarity']:.3f})")

print("\n" + "="*80)
print(f"All visualizations saved to: {VIS_DIR}/")
print("="*80)