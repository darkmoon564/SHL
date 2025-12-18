import pandas as pd
import os
from engine import engine

DATA_DIR = "d:/shl/data"
TEST_FILE = os.path.join(DATA_DIR, "test.csv")
OUTPUT_FILE = "d:/shl/predictions.csv"

def validate():
    print("Starting validation...")
    
    if not os.path.exists(TEST_FILE):
        print(f"Test file {TEST_FILE} not found.")
        return

    try:
        df = pd.read_csv(TEST_FILE)
    except Exception as e:
        print(f"Error reading test file: {e}")
        return
        
    predictions = []
    
    csv_rows = []
    
    print(f"Generating predictions for {len(df)} queries...")
    
    for index, row in df.iterrows():
        query = row['Query']
        # Return top 10 as requested
        results = engine.search(query, limit=10)
        
        for r in results:
            # Appendix 3 Format: Query, Assessment_url
            csv_rows.append({
                'Query': query,
                'Assessment_url': r['assessment_url']
            })
        
    output_df = pd.DataFrame(csv_rows)
    # Ensure correct column order
    output_df = output_df[['Query', 'Assessment_url']]
    
    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Predictions saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    validate()
