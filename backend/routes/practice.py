"""
routes/practice.py  — preptalk_practice database
Firecrawl PYQ crawler with MongoDB caching (24h TTL) + aptitude results.

Endpoints:
  GET  /api/practice/pyq/{company}     → fetch (or serve cached) PYQs
  POST /api/practice/aptitude/result   → save aptitude test result
  GET  /api/practice/aptitude/history  → list past aptitude results
"""

import os
from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel

from backend.crawler.firecrawl_api import crawler
from backend.database.database import pyq_cache_col, aptitude_col
from backend.database.models import pyq_cache_doc, aptitude_result_doc

router = APIRouter()
CACHE_TTL_HOURS = 24


# ── PYQ Endpoints ─────────────────────────────────────────

@router.get("/pyq/{company_name}")
async def get_pyq(company_name: str):
    company_key = company_name.lower()

    # Check cache in preptalk_practice → pyq_cache
    cached = await pyq_cache_col().find_one({"company": company_key}, {"_id": 0})
    if cached:
        cache_age = datetime.utcnow() - cached["cached_at"].replace(tzinfo=None) \
                    if hasattr(cached["cached_at"], "replace") else timedelta(hours=999)
        if isinstance(cache_age, timedelta) and cache_age.total_seconds() < CACHE_TTL_HOURS * 3600:
            return {
                "status":   "success",
                "source":   "cache",
                "company":  company_name,
                "questions": cached["questions"]
            }

    # Crawl via Firecrawl
    data = crawler.crawl_company_questions(company_name)

    questions = []
    if isinstance(data, dict):
        questions = data.get("questions", [])

    if not questions:
        questions = [
            f"Tell me about yourself and why {company_name}?",
            f"What do you know about {company_name}'s products and culture?",
            "Describe a challenging project you worked on.",
            "How do you handle pressure and tight deadlines?",
            "Where do you see yourself in 3 years?"
        ]

    # Save/update cache
    await pyq_cache_col().update_one(
        {"company": company_key},
        {"$set": pyq_cache_doc(company_name, questions)},
        upsert=True
    )

    return {
        "status":    "success",
        "source":    "crawled",
        "company":   company_name,
        "questions": questions
    }


# ── Aptitude Endpoints ────────────────────────────────────

class AptitudeResultRequest(BaseModel):
    user_id:  str = "guest"
    category: str           # Mixed | Quantitative | Logical | Verbal
    score:    int
    total:    int
    answers:  list = []

@router.post("/aptitude/result")
async def save_aptitude_result(req: AptitudeResultRequest):
    doc = aptitude_result_doc(req.user_id, req.category, req.score, req.total, req.answers)
    result = await aptitude_col().insert_one(doc)
    return {
        "status":     "saved",
        "category":   req.category,
        "score":      req.score,
        "total":      req.total,
        "percentage": doc["percentage"]
    }

@router.get("/aptitude/history")
async def aptitude_history(user_id: str = "guest", limit: int = 10):
    results = await aptitude_col().find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)
    return {"history": results}
