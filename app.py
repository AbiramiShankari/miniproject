"""
PrepTalk — FastAPI Entry Point
Run from project root: uvicorn app:app --reload --port 8000

Serves:
  /          → landing page (frontend/pages/login.html)
  /pages/*   → app pages (frontend/pages/)
  /static/*  → assets (frontend/static/)
  /api/*     → REST API routes
  /docs      → Swagger UI
"""
import sys, os, logging
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes import speech, sessions, communication, practice, ats, ai_coach, auth
from backend.database.database import get_client

FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")

logger = logging.getLogger("preptalk")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")


# ── MongoDB lifecycle ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    try:
        client = get_client()
        await client.admin.command("ping")
        logger.info("✅  MongoDB connected  →  %s", client.HOST if hasattr(client, 'HOST') else "localhost:27017")
    except Exception as exc:
        logger.warning("⚠️  MongoDB NOT reachable: %s  (API still starts, but DB calls will fail)", exc)

    yield  # app runs here

    # ── Shutdown ──
    try:
        get_client().close()
        logger.info("🛑  MongoDB connection closed.")
    except Exception:
        pass


app = FastAPI(
    title="PrepTalk API",
    description=(
        "AI-powered personalised interview preparation platform.\n\n"
        "**Databases:**\n"
        "- `preptalk_interviews` → sessions, evaluations, proctor_logs, chat_history\n"
        "- `preptalk_ats` → resumes, ats_results\n"
        "- `preptalk_practice` → pyq_cache, aptitude_results\n\n"
        "**AI:** Google Gemini 2.5 Flash | **Crawler:** Firecrawl"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes (must be before static mounts) ───────────────
app.include_router(sessions.router,      prefix="/api/sessions",  tags=["Interview Sessions"])
app.include_router(speech.router,        prefix="/api/speech",    tags=["Speech AI & Proctor"])
app.include_router(communication.router, prefix="/api/comm",      tags=["Communication Hub"])
app.include_router(ats.router,           prefix="/api/ats",       tags=["ATS & Resume"])
app.include_router(practice.router,      prefix="/api/practice",  tags=["Practice & PYQ"])
app.include_router(ai_coach.router,      prefix="/api/coach",     tags=["AI Coach"])
app.include_router(auth.router,          prefix="/api/auth",      tags=["Authentication"])

# ── Health + DB status endpoint ──────────────────────────────
@app.get("/api", tags=["Health"])
async def api_root():
    db_status = "unknown"
    try:
        await get_client().admin.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {e}"
    return {
        "status":    "ok",
        "message":   "PrepTalk API v2.0 ✅",
        "mongodb":   db_status,
        "frontend":  "http://localhost:8000/",
        "docs":      "http://localhost:8000/docs",
    }

# ── Serve landing/login page at root ────────────────────────
@app.get("/", include_in_schema=False)
async def serve_landing():
    return FileResponse(os.path.join(FRONTEND, "pages", "login.html"))

@app.get("/login.html", include_in_schema=False)
async def serve_login_root():
    return FileResponse(os.path.join(FRONTEND, "pages", "login.html"))

@app.get("/pages/login.html", include_in_schema=False)
async def serve_login_pages():
    return FileResponse(os.path.join(FRONTEND, "pages", "login.html"))

# ── Serve individual pages ───────────────────────────────────
@app.get("/pages/{page_name}", include_in_schema=False)
async def serve_page(page_name: str):
    path = os.path.join(FRONTEND, "pages", page_name)
    if os.path.exists(path):
        return FileResponse(path)
    return FileResponse(os.path.join(FRONTEND, "pages", "login.html"))

# Convenience redirects
@app.get("/profile",  include_in_schema=False)
async def r_profile():  return FileResponse(os.path.join(FRONTEND, "pages", "profile.html"))

@app.get("/history",  include_in_schema=False)
async def r_history():  return FileResponse(os.path.join(FRONTEND, "pages", "history.html"))

@app.get("/compare",  include_in_schema=False)
async def r_compare():  return FileResponse(os.path.join(FRONTEND, "pages", "compare.html"))

# ── Static assets ─────────────────────────────────────────────
# Mount static AFTER page routes to avoid conflicts
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND, "static")), name="static")
app.mount("/pages",  StaticFiles(directory=os.path.join(FRONTEND, "pages")),  name="pages")
