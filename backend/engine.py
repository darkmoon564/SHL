import os
import google.generativeai as genai
from pinecone import Pinecone

class RecommendationEngine:
    def __init__(self):
        self.index = None
        self.setup_cloud_services()
        
    def setup_cloud_services(self):
        # 1. Setup Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
        else:
            print("Warning: GEMINI_API_KEY not found. Search will fail.")

        # 2. Setup Pinecone
        pc_key = os.getenv("PINECONE_API_KEY")
        if pc_key:
            try:
                pc = Pinecone(api_key=pc_key)
                self.index = pc.Index("shl-assessments")
            except Exception as e:
                 print(f"Pinecone Connection Error: {e}")
        else:
            print("Warning: PINECONE_API_KEY not found. Search will fail.")

    def search(self, query: str, limit: int = 10):
        if not self.index:
            print("Error: Pinecone index not initialized.")
            return []

        try:
            # 1. Generate Query Embedding using Gemini
            # Model must match the one used for ingestion
            result = genai.embed_content(
                model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = result['embedding']
            
            # 2. Search Pinecone
            # Fetch more than limit to allow for balancing if needed
            search_response = self.index.query(
                vector=query_embedding,
                top_k=limit * 2, 
                include_metadata=True
            )
            
            # 3. Process Results
            matches = search_response['matches']
            results = []
            
            for match in matches:
                # Map metadata back to our internal structure
                md = match['metadata']
                results.append({
                    "assessment_name": md.get('name', ''),
                    "assessment_url": md.get('url', ''),
                    "test_type": md.get('test_type', ''),
                    "description": md.get('description', ''),
                    "score": match['score']
                })
            
            # 4. Balance Results (Same logic as before, but on retrieved candidates)
            final_results = self._balance_results(results, query, limit)
            return final_results

        except Exception as e:
            print(f"Search Error: {e}")
            return []

    def _balance_results(self, candidates, query, limit):
        # Reuse existing balancing logic concepts
        # Identify intent
        query_lower = query.lower()
        soft_keywords = ['collaborat', 'communicat', 'team', 'lead', 'person', 'behav', 'soft', 'manag']
        needs_soft = any(k in query_lower for k in soft_keywords)
        
        hard_skills = []
        soft_skills = []
        
        for item in candidates:
            # Categorize
            t_type = item.get('test_type', '').upper()
            if any(x in t_type for x in ['P', 'B', 'A', 'E', 'D', 'C']):
                soft_skills.append(item)
            else:
                hard_skills.append(item)
                
        # If no explicit need for soft skills, just return top K (natural order)
        # But if needs_soft is True, ensure we mix them
        
        final_list = []
        if needs_soft and hard_skills and soft_skills:
            # Interleave: 2 Hard, 1 Soft, etc. or 1:1 depending on ratio
            h_idx, s_idx = 0, 0
            while len(final_list) < limit:
                # Add Hard
                if h_idx < len(hard_skills):
                    final_list.append(hard_skills[h_idx])
                    h_idx += 1
                if len(final_list) >= limit: break
                
                # Add Soft
                if s_idx < len(soft_skills):
                    final_list.append(soft_skills[s_idx])
                    s_idx += 1
        else:
            # Default ranking
            final_list = candidates[:limit]
            
        return final_list

# Initialize
engine = RecommendationEngine()
