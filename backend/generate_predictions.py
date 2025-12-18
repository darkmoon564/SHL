import pandas as pd
import sys
import os

# Add current directory to path so we can import engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import engine

def generate_predictions():
    input_file = "d:/shl/data/test.csv"
    output_file = "d:/shl/antigravity_ai.csv"
    
    print(f"Reading test data from {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if "Query" not in df.columns:
        print("Error: 'Query' column not found in test.csv")
        return

    queries = df["Query"].tolist()
    results = []
    
    print(f"Processing {len(queries)} queries...")
    
    for i, q in enumerate(queries):
        if pd.isna(q) or not str(q).strip():
            continue
            
        # Get Top 10 recommendations
        recs = engine.search(str(q), limit=10)
        
        for r in recs:
            results.append({
                "Query": q,
                "Assessment_url": r["assessment_url"]
            })
            
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(queries)}")

    if not results:
        print("No results generated.")
        return

    output_df = pd.DataFrame(results)
    output_df.to_csv(output_file, index=False)
    print(f"Successfully saved {len(output_df)} predictions to {output_file}")

if __name__ == "__main__":
    generate_predictions()
