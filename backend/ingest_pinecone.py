import json
import os
import time
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

# Configuration
DATA_FILE = "d:/shl/data/assessments.json"
PINECONE_INDEX_NAME = "shl-assessments"
EMBEDDING_MODEL = "models/embedding-001"

def ingest():
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return
        
    with open(DATA_FILE, "r") as f:
        assessments = json.load(f)
    print(f"Loaded {len(assessments)} assessments.")

    # 2. Setup Gemini (Embeddings)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return
    genai.configure(api_key=api_key)

    # 3. Setup Pinecone (Vector DB)
    pc_key = os.getenv("PINECONE_API_KEY")
    if not pc_key:
        print("Error: PINECONE_API_KEY environment variable not set.")
        return
    
    pc = Pinecone(api_key=pc_key)
    
    # Create index if not exists
    existing_indexes = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating index '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768, # Gemini embedding dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait for index to be ready
        while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
            time.sleep(1)
            
    index = pc.Index(PINECONE_INDEX_NAME)

    # 4. Generate Embeddings & Upsert
    print("Generating embeddings and uploading to Pinecone...")
    
    batch_size = 50
    for i in tqdm(range(0, len(assessments), batch_size)):
        batch = assessments[i:i+batch_size]
        vectors = []
        
        # Prepare text for embedding
        texts = [f"{item['assessment_name']} {item.get('description', '')}" for item in batch]
        
        try:
            # Batch embedding call to Gemini
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=texts,
                task_type="retrieval_document"
            )
            embeddings = result['embedding']
            
            # Prepare vectors for Pinecone
            for j, item in enumerate(batch):
                # We need a unique ID. Using URL slug or fallback to index
                uid = item.get('assessment_url', '').split('/')[-2] 
                if not uid: uid = f"doc_{i+j}"
                
                vectors.append({
                    "id": uid,
                    "values": embeddings[j],
                    "metadata": {
                        "name": item.get('assessment_name', ''),
                        "url": item.get('assessment_url', ''),
                        "test_type": item.get('test_type', ''),
                        "description": item.get('description', '')[:1000] # Truncate if too long
                    }
                })
                
            # Upsert batch
            index.upsert(vectors=vectors)
            
        except Exception as e:
            print(f"Error processing batch {i}: {e}")
            
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest()
