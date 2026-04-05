# AI Research Analyst

A multi-agent AI system that analyzes research documents using parallel AI agents. Built with FastAPI, Streamlit, and Ollama.

## Features

- **Research Analysis** - Paste text or upload documents for multi-agent analysis with plan, insights, charts, and PDF export
- **Chat with Document** - Upload a document or paste text, then ask questions with RAG-powered retrieval
- **Compare Documents** - Upload 2+ documents for structured comparison of themes, findings, and differences
- **Sentiment & Tone Analysis** - Polarity and subjectivity gauge charts using TextBlob
- **Topic Modeling** - LDA-based topic discovery with visualization
- **Research Timeline** - Automatic date extraction and chronological event display
- **Citation Extraction** - Detects references and links to Google Scholar
- **Web Search** - Finds related papers and articles via DuckDuckGo
- **Agent Activity Log** - Real-time view of what each AI agent is doing
- **PDF Export** - Styled downloadable reports with charts and citations
- **Authentication** - Register, login, or continue as guest
- **History** - All analyses auto-saved with sidebar navigation
- **Docker Support** - One command to run the entire stack

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM | Ollama (llama3:instruct) |
| RAG | ChromaDB + Sentence Transformers |
| Database | SQLite |
| NLP | TextBlob, scikit-learn (LDA) |
| PDF | fpdf2 |
| Containerization | Docker + Docker Compose |

## Project Structure

```
ai-research-analyst/
├── backend/
│   ├── main.py                 # FastAPI app with all endpoints
│   ├── auth.py                 # Authentication & SQLite storage
│   ├── Dockerfile
│   └── agents/
│       ├── planner.py          # Research planning agent
│       ├── researcher.py       # Text analysis agent
│       ├── insight.py          # Insight extraction agent
│       ├── comparator.py       # Document comparison agent
│       ├── rag.py              # RAG with ChromaDB + embeddings
│       ├── web_search.py       # DuckDuckGo search agent
│       ├── llm.py              # Ollama LLM wrapper
│       └── utils.py            # Text chunking & file extraction
├── frontend/
│   ├── app.py                  # Streamlit UI
│   └── Dockerfile
├── .streamlit/
│   └── config.toml             # Streamlit theme config
├── docker-compose.yml          # Ollama + Backend + Frontend
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running
- llama3:instruct model pulled: `ollama pull llama3:instruct`

### Local Development

```bash
# Clone the repo
git clone https://github.com/yourusername/ai-research-analyst.git
cd ai-research-analyst

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend (terminal 1)
uvicorn backend.main:app --reload

# Start the frontend (terminal 2)
streamlit run frontend/app.py
```

The app will be available at `http://localhost:8501`

### Docker

```bash
# Start all services
docker-compose up --build

# Pull the LLM model (first time only)
docker exec ollama ollama pull llama3:instruct
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Multi-agent research analysis |
| `/rag/upload` | POST | Upload document for RAG |
| `/rag/query` | POST | Ask questions about uploaded document |
| `/rag/reset` | POST | Clear document store |
| `/compare` | POST | Compare multiple documents |
| `/auth/register` | POST | Create new account |
| `/auth/login` | POST | Login |
| `/history/save` | POST | Save analysis to history |
| `/history/{username}` | GET | Get user's history |
| `/history/detail/{id}` | GET | Get full analysis by ID |
| `/history/{id}` | DELETE | Delete analysis |

## Architecture

```
User Input
    │
    ├── Research Analysis
    │   ├── Planner Agent → research strategy
    │   ├── Researcher Agent → parallel chunk analysis
    │   ├── Insight Agent → patterns & findings
    │   └── Web Search Agent → related papers
    │
    ├── Chat with Document (RAG)
    │   ├── Document → chunked → embedded (Sentence Transformers)
    │   ├── Stored in ChromaDB vector store
    │   └── Query → semantic search → LLM answer with sources
    │
    └── Compare Documents
        ├── Each document → summarized by LLM
        └── All summaries → structured comparison
```

## Screenshots

| Landing Page | Research Analysis | Chat with Document |
|---|---|---|
| Mode selection cards | Multi-tab results with charts | RAG-powered Q&A |
