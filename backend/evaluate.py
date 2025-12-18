import pandas as pd
from engine import engine
import numpy as np

TRAIN_FILE = "../data/train.csv"

def normalize_url(url):
    # Remove trailing slash and split
    parts = url.strip().rstrip('/').split('/')
    # Return the last part (slug)
    return parts[-1]

def calculate_recall_at_k(truth_urls, predicted_urls, k=10):
    # Truncate predictions to top K
    predicted_at_k = predicted_urls[:k]
    
    # Normalize everything
    norm_truth = {normalize_url(u) for u in truth_urls}
    norm_pred = [normalize_url(u) for u in predicted_at_k]
    
    # Relevant items found in top K
    relevant_found = [slug for slug in norm_pred if slug in norm_truth]
    
    if not truth_urls:
        return 0.0
        
    return len(relevant_found) / len(truth_urls)

def evaluate():
    print("Loading training data...")
    try:
        df = pd.read_csv(TRAIN_FILE)
    except Exception as e:
        print(f"Error reading train file: {e}")
        return

    # Group by Query to get all relevant URLs for a single query
    # The train.csv format seems to be Long Format (Query is repeated)
    grouped = df.groupby('Query')['Assessment_url'].apply(list).reset_index()
    
    recalls = []
    
    print(f"Evaluating on {len(grouped)} unique queries...")
    
    for _, row in grouped.iterrows():
        query = row['Query']
        truth_urls = row['Assessment_url']
        
        # Get predictions
        results = engine.search(query, limit=10)
        predicted_urls = [r['assessment_url'] for r in results]
        
        recall = calculate_recall_at_k(truth_urls, predicted_urls, k=10)
        recalls.append(recall)
        
        # Optional: Print detail for debugging
        # print(f"Query: {query[:30]}... | Recall@10: {recall:.2f}")

    mean_recall = np.mean(recalls)
    print(f"\nMean Recall@10: {mean_recall:.4f}")
    
    return mean_recall

if __name__ == "__main__":
    evaluate()
