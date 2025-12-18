from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
try:
    from engine import engine
except ImportError:
    from .engine import engine

app = FastAPI(title="SHL Assessment Recommender")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    url: Optional[str] = None

class AssessmentResult(BaseModel):
    assessment_name: str
    assessment_url: str
    score: float

@app.post("/recommend", response_model=List[AssessmentResult])
async def recommend(request: QueryRequest):
    # If URL is provided, we might want to scrape it. 
    # For now, we'll treat the query as the primary input.
    # If query is empty but URL is there, we'd need to fetch URL content.
    # (Future task: fetch JD from URL)
    
    text = request.query
    if not text and request.url:
         # Placeholder for URL scraping
         text = "JD content from " + request.url
    
    if not text:
        raise HTTPException(status_code=400, detail="Query or URL required")
        
    results = engine.search(text)
    return results

@app.get("/health")
def health():
    return {"status": "ok", "assessments_loaded": len(engine.assessments)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
