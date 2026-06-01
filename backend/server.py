"""
FastAPI backend for the Ed Discussion tutor assistant.

Startup:
    cp .env.example .env          # fill in ANTHROPIC_API_KEY
    cp ../path/to/qa.json ../data/qa.json
    pip install -r requirements.txt
    uvicorn server:app --reload --port 8765
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

import search as search_module
import generate as generate_module


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_path = os.environ.get("DATA_PATH", "../data/qa.json")
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), data_path))
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Knowledge base not found at {data_path}. "
            "Copy your anonymised Q&A JSON to data/qa.json"
        )
    search_module.load_knowledge_base(data_path)
    yield


app = FastAPI(title="Ed Tutor Assistant", lifespan=lifespan)

# Allow requests from the Chrome extension (chrome-extension://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class SuggestRequest(BaseModel):
    title: str
    body: str


class MatchedThread(BaseModel):
    number: int | None
    title: str
    question: str
    answers: list[str]
    score: float


class SuggestResponse(BaseModel):
    suggested_answer: str
    matched_threads: list[MatchedThread]


@app.get("/health")
def health():
    return {"status": "ok", "indexed": len(search_module._records)}


@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: SuggestRequest):
    if not req.title.strip() and not req.body.strip():
        raise HTTPException(status_code=400, detail="Title and body cannot both be empty.")

    top_k = int(os.environ.get("TOP_K", 3))
    query = f"{req.title} {req.body}"
    matches = search_module.search(query, top_k=top_k)

    if not matches:
        raise HTTPException(status_code=404, detail="No matching records found.")

    answer = generate_module.generate_answer(req.title, req.body, matches)

    return SuggestResponse(
        suggested_answer=answer,
        matched_threads=[MatchedThread(**m) for m in matches],
    )
