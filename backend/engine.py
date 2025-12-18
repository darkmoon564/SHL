import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

DATA_FILE = "d:/shl/data/assessments.json"

class RecommendationEngine:
    def __init__(self):
        self.assessments = []
        self.embeddings = None
        self.model = None
        self.load_data()
        
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            print(f"Warning: {DATA_FILE} not found. Engine will be empty.")
            return

        with open(DATA_FILE, "r") as f:
            self.assessments = json.load(f)
            
        print(f"Loaded {len(self.assessments)} assessments.")
        
        # Categorize assessments
        for item in self.assessments:
            t_type = item.get('test_type', '').upper()
            if any(x in t_type for x in ['K', 'S']):
                item['category'] = 'Hard'
            else:
                item['category'] = 'Soft'
        
        # Initialize model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Pre-compute embeddings
        print("Generating embeddings...")
        corpus = [f"{item['assessment_name']} {item.get('description', '')}" for item in self.assessments]
        self.embeddings = self.model.encode(corpus)
        print("Embeddings ready.")

    def search(self, query: str, limit: int = 10):
        if not self.assessments:
            return []
            
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top 30 candidates to have a pool for balancing
        top_indices = np.argsort(similarities)[::-1][:30]
        
        candidates = []
        for idx in top_indices:
            item = self.assessments[idx].copy()
            item['score'] = float(similarities[idx])
            candidates.append(item)
            
        return self._balance_results(candidates, query, limit)

    def _balance_results(self, candidates, query, limit):
        if not candidates:
            return []
            
        # Separate into categories
        hard_items = [c for c in candidates if c['category'] == 'Hard']
        soft_items = [c for c in candidates if c['category'] == 'Soft']
        
        # Simple heuristic: Check for obvious soft skill keywords in query
        soft_keywords = ['team', 'collaborat', 'communicat', 'lead', 'manag', 'person', 'behav', 'soft', 'interpersonal', 'cultur']
        query_lower = query.lower()
        needs_soft = any(k in query_lower for k in soft_keywords)
        
        results = []
        
        # Logic:
        # 1. Always take the absolute best match (score likely highest).
        # 2. If 'needs_soft' is true, try to interleave Soft items if they are reasonable.
        # 3. Otherwise, just ensure we don't return 100% homogenous results IF the other category has decent candidates.
        
        # Strategy: Pick top items, but force at least some ratio if candidates exist.
        
        # If user explicitly asks for mixed skills (inferred from needs_soft and presence of hard skills implied by results),
        # we aim for a mix.
        
        # If we have both types available with decent scores:
        if hard_items and soft_items:
            best_hard_score = hard_items[0]['score']
            best_soft_score = soft_items[0]['score']
            
            # If scores are comparable (within 20%), force mix
            score_diff = abs(best_hard_score - best_soft_score)
            comparable = score_diff < 0.15 
            
            if comparable or needs_soft:
                # Interleave approach
                h_idx, s_idx = 0, 0
                while len(results) < limit:
                    # Pick Hard
                    if h_idx < len(hard_items):
                        results.append(hard_items[h_idx])
                        h_idx += 1
                    
                    if len(results) >= limit: break
                    
                    # Pick Soft
                    if s_idx < len(soft_items):
                        results.append(soft_items[s_idx])
                        s_idx += 1
                        
                    if h_idx >= len(hard_items) and s_idx >= len(soft_items):
                        break
            else:
                # One category is clearly dominant, just return by score
                results = candidates[:limit]
        else:
             results = candidates[:limit]

        # Deduplicate just in case (though indices are unique)
        return results[:limit]

# Singleton instance
engine = RecommendationEngine()
