from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import time
import datetime

from backend.agents.planner import plan_task
from backend.agents.researcher import analyze_chunk
from backend.agents.insight import generate_insights
from backend.agents.web_search import search_related_papers
from backend.agents.utils import split_text, extract_text_from_bytes
from backend.agents.rag import DocumentStore, EmbeddingService
from backend.agents.comparator import summarize_document, compare_documents
from backend.agents.llm import call_llm
from backend.auth import (
    create_user, authenticate_user, create_access_token,
    get_current_user, init_db, save_analysis, get_user_history,
    get_analysis_by_id, delete_analysis
)

app = FastAPI()

# Initialize database and document store
init_db()
doc_store = DocumentStore()


class ResearchRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    question: str
    collection_name: str = "default"


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""


@app.post("/analyze")
def analyze(req: ResearchRequest):
    text = req.text
    activity_log = []

    def log_step(agent: str, action: str, status: str = "completed"):
        activity_log.append({
            "agent": agent,
            "action": action,
            "status": status,
            "timestamp": time.time()
        })

    MAX_WORDS = 5000
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        log_step("System", f"Text trimmed to {MAX_WORDS} words")

    log_step("System", f"Received {len(text.split())} words for analysis")

    # Step 1: Planner agent
    log_step("Planner Agent", "Creating research strategy...", "running")
    plan = plan_task(text)
    log_step("Planner Agent", "Research plan created")

    # Step 2: Researcher agent (parallel chunk analysis)
    chunks = split_text(text)
    log_step("Researcher Agent", f"Splitting text into {len(chunks)} chunks for parallel analysis")

    with ThreadPoolExecutor() as executor:
        log_step("Researcher Agent", "Analyzing chunks in parallel...", "running")
        results = list(executor.map(analyze_chunk, chunks))

    combined = "\n".join(results)
    log_step("Researcher Agent", f"Analysis complete — {len(chunks)} chunks processed")

    # Step 3: Insight agent
    log_step("Insight Agent", "Extracting patterns and key findings...", "running")
    insights = generate_insights(combined)
    log_step("Insight Agent", "Key insights extracted")

    # Step 4: Web search agent
    log_step("Web Search Agent", "Searching for related papers and news...", "running")
    web_results = search_related_papers(text)
    log_step("Web Search Agent", f"Found {len(web_results)} related results")

    log_step("System", "All agents completed successfully")

    return {
        "plan": plan,
        "analysis": combined,
        "insights": insights,
        "web_results": web_results,
        "activity_log": activity_log
    }


# ---------- AUTH ENDPOINTS ----------
@app.post("/auth/register")
def register(req: RegisterRequest):
    user = create_user(req.username, req.password, req.full_name)
    if not user:
        raise HTTPException(status_code=400, detail="Username already exists")
    token = create_access_token(user["username"])
    return {"token": token, "user": user}


@app.post("/auth/login")
def login(req: RegisterRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user["username"])
    return {"token": token, "user": user}


# ---------- HISTORY ENDPOINTS ----------
@app.post("/history/save")
def history_save(
    data: dict,
):
    username = data.get("username", "")
    if not username:
        raise HTTPException(status_code=401, detail="Username required")
    analysis_id = save_analysis(
        username=username,
        input_text=data.get("input_text", ""),
        plan=data.get("plan", ""),
        analysis=data.get("analysis", ""),
        insights=data.get("insights", ""),
        web_results=data.get("web_results", [])
    )
    return {"status": "ok", "analysis_id": analysis_id}


@app.get("/history/{username}")
def history_list(username: str):
    return get_user_history(username)


@app.get("/history/detail/{analysis_id}")
def history_detail(analysis_id: int):
    result = get_analysis_by_id(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@app.delete("/history/{analysis_id}")
def history_delete(analysis_id: int):
    delete_analysis(analysis_id)
    return {"status": "ok"}


@app.post("/rag/upload")
async def rag_upload(
    file: UploadFile = File(...),
    collection_name: str = "default"
):
    content = await file.read()
    text = extract_text_from_bytes(file.filename, content)

    if not text.strip():
        return {"status": "error", "message": "Could not extract text from file"}

    num_chunks = doc_store.add_document(
        doc_id=file.filename,
        text=text,
        collection_name=collection_name
    )

    return {
        "status": "ok",
        "doc_id": file.filename,
        "num_chunks": num_chunks,
        "word_count": len(text.split())
    }


@app.post("/rag/query")
def rag_query(req: ChatRequest):
    sources = doc_store.query(
        question=req.question,
        collection_name=req.collection_name,
        n_results=5
    )

    if not sources:
        return {
            "answer": "No relevant content found. Please upload a document first.",
            "sources": []
        }

    context = "\n\n".join([s["text"] for s in sources])

    prompt = f"""Based on the following context from the uploaded document(s), answer the question.
If the answer is not found in the context, say so clearly.

Context:
{context}

Question: {req.question}

Answer:"""

    answer = call_llm(prompt)

    return {
        "answer": answer,
        "sources": sources
    }


@app.post("/rag/reset")
def rag_reset(collection_name: str = "default"):
    doc_store.reset(collection_name)
    return {"status": "ok", "message": "Document store cleared"}


@app.post("/compare")
async def compare(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        return {"status": "error", "message": "Please upload at least 2 documents"}

    doc_summaries = {}
    doc_texts = {}

    for file in files:
        content = await file.read()
        text = extract_text_from_bytes(file.filename, content)
        doc_texts[file.filename] = text
        summary = summarize_document(text, file.filename)
        doc_summaries[file.filename] = summary

    comparison = compare_documents(doc_summaries)

    return {
        "summaries": doc_summaries,
        "comparison": comparison,
        "doc_names": list(doc_summaries.keys())
    }
