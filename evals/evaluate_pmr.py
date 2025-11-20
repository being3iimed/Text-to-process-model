import os
import csv
import glob
from pathlib import Path

# Try to import tiktoken, otherwise fallback to simple split
try:
    import tiktoken
    ENCODING = tiktoken.get_encoding("cl100k_base")
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    print("Warning: tiktoken not found. Using whitespace splitting for token count approximation.")

# Configuration
BASE_DIR = Path("evals")
MODELS = {
    "mistral-large": BASE_DIR / "mistral-large",
    "mistral-medium": BASE_DIR / "mistral-medium",
    "bpmn_gold": BASE_DIR / "bpmn_gold"
}

OUTPUT_FILE = BASE_DIR / "pmr_evaluation.csv"

def count_tokens(text):
    """Counts tokens using tiktoken or fallback."""
    if HAS_TIKTOKEN:
        return len(ENCODING.encode(text))
    else:
        # Fallback: simple whitespace split
        return len(text.split())

def evaluate_model_tokens(model_dir):
    """Calculates average token count for a specific model directory."""
    if not model_dir.exists():
        print(f"Directory not found: {model_dir}")
        return 0

    bpmn_files = list(model_dir.glob("*.bpmn"))
    if not bpmn_files:
        print(f"No .bpmn files found in {model_dir}")
        return 0

    total_tokens = 0
    file_count = len(bpmn_files)

    for bpmn_file in bpmn_files:
        try:
            with open(bpmn_file, 'r', encoding='utf-8') as f:
                content = f.read()
                total_tokens += count_tokens(content)
        except Exception as e:
            print(f"Error reading {bpmn_file}: {e}")

    return total_tokens / file_count if file_count > 0 else 0

def calculate_compact_grade(avg_tokens, gold_tokens):
    """Calculates compact grade relative to gold standard (Grade 2)."""
    if gold_tokens == 0:
        return 2
    
    # If tokens are fewer (more compact), grade increases.
    # If tokens are more (less compact), grade decreases.
    # Baseline: Gold = 2 points.
    # Logic: Grade = 2 * (Gold / Generated)
    # Capped at 5, minimum 1.
    
    ratio = gold_tokens / avg_tokens if avg_tokens > 0 else 1
    grade = 2 * ratio
    
    # Round to nearest 0.5 or integer? Let's do 2 decimal places for precision then round for display if needed.
    # User table has integers/halves (e.g. 3.33, 3.50).
    return min(5.0, max(1.0, grade))

def main():
    results = []
    token_counts = {}
    
    print("Starting PMR evaluation...")
    
    # First pass: Calculate tokens for all models
    for model_name, model_dir in MODELS.items():
        print(f"Evaluating {model_name}...")
        token_counts[model_name] = evaluate_model_tokens(model_dir)

    gold_tokens = token_counts.get("bpmn_gold", 0)
    if gold_tokens == 0:
        print("Warning: bpmn_gold has 0 tokens. Compact grades may be inaccurate.")

    # Second pass: Generate metrics
    for model_name in MODELS.keys():
        avg_tokens = token_counts.get(model_name, 0)
        
        # Calculate Compact grade
        if model_name == "bpmn_gold":
            compact_grade = 2.0 # Baseline
        else:
            compact_grade = calculate_compact_grade(avg_tokens, gold_tokens)

        metrics = {
            "PMR": model_name,
            "Avg. Token Count": f"{avg_tokens:.2f}",
            "Compact": f"{compact_grade:.2f}",
            "Expressive": "5 (100%)", # Static
            "Human readable": 2, # Static
            "Vizualisable": 3, # Static
            "Usable": 4, # Static
            "Extensible": 5 # Static
        }
        results.append(metrics)

    if not results:
        print("No results generated.")
        return

    # Define columns
    columns = [
        "PMR", "Avg. Token Count", "Compact", "Expressive", 
        "Human readable", "Vizualisable", "Usable", "Extensible"
    ]

    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nSuccessfully saved PMR evaluation to: {OUTPUT_FILE}")
        
        # Print preview
        print("\nEvaluation Results:")
        header_str = " | ".join(columns)
        print(header_str)
        print("-" * len(header_str))
        for row in results:
            print(" | ".join(str(row[col]) for col in columns))
            
    except Exception as e:
        print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    main()
