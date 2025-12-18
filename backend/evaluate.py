import pandas as pd
import numpy as np
import os
import re

# We will measure Mean Recall@K
# Since we don't have a perfect ground truth mapping for every possible query, 
# and the provided 'train.csv' has specific URLs, we can use that as our "Test Set" for accuracy measurement.
# For each query in train.csv, we check if the EXPECTED Assessment_url is present in the Top K recommendations.

DATA_FILE = "d:/shl/data/assessments.json"
TRAIN_FILE = "d:/shl/data/train.csv"
K = 10

from engine import engine

def normalize_url(url):
    """Normalize URL to handle minor variations (e.g. trailing slash, https vs http)"""
    if not url: return ""
    # Extract the last part of the path (slug) which is usually the ID
    # e.g. /products/product-catalog/view/assessment-name/ -> assessment-name
    parts = [p for p in url.split('/') if p]
    if parts:
        return parts[-1].lower()
    return url.lower()

def calculate_recall_at_k(engine, k=10):
    if not os.path.exists(TRAIN_FILE):
        print(f"Error: {TRAIN_FILE} not found.")
        return 0.0

    df = pd.read_csv(TRAIN_FILE)
    
    # Ensure expected columns exist
    if 'Query' not in df.columns or 'Assessment_url' not in df.columns:
        print(f"Error: {TRAIN_FILE} must have 'Query' and 'Assessment_url' columns.")
        return 0.0

    print(f"Loading training data from {TRAIN_FILE}...")
    
    # Group by Query because one query might have multiple relevant assessments?
    # In this dataset, it looks like 1-to-1 or 1-to-many. 
    # Let's verify recall: For each unique query, did we find the relevant URL in top K?
    
    hits = 0
    total_queries = 0
    
    unique_queries = df['Query'].unique()
    
    # Optimization: Loading engine is done outside loop
    
    for query in unique_queries[:50]: # Limit to 50 for quick evaluation check
        relevant_urls = df[df['Query'] == query]['Assessment_url'].tolist()
        normalized_relevant = [normalize_url(u) for u in relevant_urls]
        
        # Get recommendations
        # Note: Engine logic has changed to return dicts
        results = engine.search(query, limit=k)
        
        top_k_urls = [r['assessment_url'] for r in results]
        normalized_top_k = [normalize_url(u) for u in top_k_urls]
        
        # Check if ANY relevant URL is in the Top K
        match = any(u in normalized_top_k for u in normalized_relevant)
        
        if match:
            hits += 1
        else:
            # Debugging - print first miss
             if total_queries == 0:
                 pass
                 # print(f"Miss for '{query}': Expected {normalized_relevant}, Got {normalized_top_k}")

        total_queries += 1
        
    if total_queries == 0:
        return 0.0
        
    recall = hits / total_queries
    print(f"Evaluating on {total_queries} unique queries...")
    print(f"\nMean Recall@{k}: {recall:.4f}")
    return recall

if __name__ == "__main__":
    calculate_recall_at_k(engine, K)
