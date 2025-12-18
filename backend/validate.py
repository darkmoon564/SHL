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
    
    print(f"Generating predictions for {len(df)} queries...")
    
    for index, row in df.iterrows():
        query = row['Query']
        results = engine.search(query, limit=5)
        
        # Format: Comma separated list of recommendations? 
        # The prompt says "return a list... tabular format" for the App.
        # But for the CSV "1-csv file with 2 columns query and predictions".
        # Format usually implies a string representation of the list.
        # I'll join titles or IDs. IDs are safer.
        
        preds_str = " | ".join([f"{r['assessment_name']} ({r['assessment_url']})" for r in results])
        predictions.append(preds_str)
        
    output_df = pd.DataFrame({
        'Query': df['Query'],
        'predictions': predictions
    })
    
    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Predictions saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    validate()
