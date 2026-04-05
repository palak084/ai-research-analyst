from fastapi import FastAPI
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor

from backend.agents.planner import plan_task
from backend.agents.researcher import analyze_chunk
from backend.agents.insight import generate_insights
from backend.agents.utils import split_text

app = FastAPI()

class ResearchRequest(BaseModel):
    text: str

@app.post("/analyze")
def analyze(req: ResearchRequest):
    text = req.text

    # Safety limit
    MAX_WORDS = 5000
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])

    plan = plan_task(text)

    chunks = split_text(text)

    # Parallel agents
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(analyze_chunk, chunks))

    combined = "\n".join(results)

    insights = generate_insights(combined)

    return {
        "plan": plan,
        "analysis": combined,
        "insights": insights
    }