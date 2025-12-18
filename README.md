# SHL Assessment Recommendation System

An intelligent recommendation engine that suggests relevant SHL assessments based on natural language queries or job descriptions.

## Project Structure
- `backend/`: Python source code.
  - `scrape.py`: Robust `requests`-based script to crawl the SHL catalog.
  - `engine.py`: Recommendation core using `sentence-transformers` & Semantic Search with Balance Logic.
  - `main.py`: FastAPI Server.
  - `validate.py`: Script to generate predictions for the test set.
- `frontend/`: React + Vite + TailwindCSS Web Application.
- `data/`: 
  - `assessments.json`: The knowledge base (scraped data).
  - `train.csv` & `test.csv`: datasets for validation.

## How to Run

### Prerequisites
- Python 3.9+
- Node.js 16+

### 1. Data Ingestion (Scraping)
This step fetches the latest data from SHL. (Pre-scraped data is already in `data/assessments.json`).
```bash
# From d:/shl root
python backend/scrape.py
```
*Output*: `data/assessments.json` (~377 items).

### 2. Start the Backend API
This server loads the data and the AI model (`all-MiniLM-L6-v2`) to serve recommendations.
```bash
# From d:/shl root
python backend/main.py
```
*   Server runs at: `http://localhost:8000`
*   Docs: `http://localhost:8000/docs`

### 3. Start the Frontend Application
This launches the web interface.
```bash
# Open a new terminal
cd frontend
npm install
npm run dev
```
*   App runs at: `http://localhost:5173` (or port shown in terminal).

### 4. Run Validation (Optional)
To generate the prediction CSV for the test set:
```bash
# From d:/shl root
python backend/validate.py
```
*Output*: `predictions.csv`.

## Architecture Details
- **Scraper**: Python `requests` + `BeautifulSoup`. Concurrent fetching.
- **Engine**: Sentence Transformers for Embeddings + Cosine Similarity.
- **Balancing**: Custom logic to interleave "Hard Skill" and "Soft Skill" assessments for mixed queries.
- **Frontend**: React (Vite) with Table view and direct links to SHL.
