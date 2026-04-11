"""
PrepTalk — MongoDB connection manager
Uses Motor (async) with a single shared client.

Three separate databases:
  preptalk_interviews  → sessions, evaluations, proctor_logs, chat_history
  preptalk_ats         → resumes, ats_results
  preptalk_practice    → pyq_cache, aptitude_results

SETUP:
  Option A (Local): Install MongoDB Community from https://www.mongodb.com/try/download/community
  Option B (Cloud):  Create a free Atlas cluster at https://cloud.mongodb.com
                     then set MONGO_URI in .env to your Atlas connection string
"""

import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load .env from the backend/ directory (works regardless of launch CWD)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

MONGO_URI     = os.getenv("MONGO_URI",           "mongodb://localhost:27017")
DB_INTERVIEWS = os.getenv("MONGO_DB_INTERVIEWS", "preptalk_interviews")
DB_ATS        = os.getenv("MONGO_DB_ATS",        "preptalk_ats")
DB_PRACTICE   = os.getenv("MONGO_DB_PRACTICE",   "preptalk_practice")

_client: AsyncIOMotorClient = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,   # fail fast if MongoDB is not running
            connectTimeoutMS=5000,
        )
    return _client

# ── Database handles ──────────────────────────────────────
def interview_db(): return get_client()[DB_INTERVIEWS]
def ats_db():       return get_client()[DB_ATS]
def practice_db():  return get_client()[DB_PRACTICE]

# ── Collection handles — interviews ───────────────────────
def sessions_col():     return interview_db()["sessions"]
def evaluations_col():  return interview_db()["evaluations"]
def proctor_logs_col(): return interview_db()["proctor_logs"]
def chat_history_col(): return interview_db()["chat_history"]

# ── Collection handles — ATS ──────────────────────────────
def resumes_col():      return ats_db()["resumes"]
def ats_results_col():  return ats_db()["ats_results"]

# ── Collection handles — practice ─────────────────────────
def pyq_cache_col():    return practice_db()["pyq_cache"]
def aptitude_col():     return practice_db()["aptitude_results"]
