from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import speech, sessions, communication, practice, ats, ai_coach

app = FastAPI(
    title="PrepTalk API",
    description=(
        "AI-powered personalised interview preparation platform.\n\n"
        "**Databases:**\n"
        "- `preptalk_interviews` → sessions, evaluations, proctor_logs, chat_history\n"
        "- `preptalk_ats` → resumes, ats_results\n"
        "- `preptalk_practice` → pyq_cache, aptitude_results\n\n"
        "**AI:** Google Gemini 1.5 Flash | **Crawler:** Firecrawl"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(sessions.router,      prefix="/api/sessions",  tags=["Interview Sessions"])
app.include_router(speech.router,        prefix="/api/speech",    tags=["Speech AI & Proctor"])
app.include_router(communication.router, prefix="/api/comm",      tags=["Communication Hub"])
app.include_router(ats.router,           prefix="/api/ats",       tags=["ATS & Resume"])
app.include_router(practice.router,      prefix="/api/practice",  tags=["Practice & PYQ"])
app.include_router(ai_coach.router,      prefix="/api/coach",     tags=["AI Coach"])


# ── Health ─────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status":    "ok",
        "message":   "PrepTalk API v2.0 ✅",
        "databases": {
            "interviews": "preptalk_interviews",
            "ats":        "preptalk_ats",
            "practice":   "preptalk_practice",
        }
    }
