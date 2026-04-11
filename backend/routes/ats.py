"""
routes/ats.py  — preptalk_ats database
Handles resume upload, AI-powered ATS scoring, and self-intro generation.

Endpoints:
  POST /api/ats/analyze    → AI ATS score + save resume + result
  GET  /api/ats/history    → list past ATS analyses
  GET  /api/ats/{resume_id} → full ATS result for a resume
"""

import os, json, uuid
from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from backend.database.database import resumes_col, ats_results_col
from backend.database.models import resume_doc, ats_result_doc

load_dotenv()
router = APIRouter()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


# ── Schemas ───────────────────────────────────────────────
class ATSRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    user_id:     str = "guest"

class ATSResponse(BaseModel):
    resume_id:        str
    ats_score:        int
    keyword_score:    int
    format_score:     int
    experience_score: int
    present_keywords: list[str]
    missing_keywords: list[str]
    strengths:        list[str]
    improvements:     list[str]
    overall_feedback: str
    self_intro_draft: str


# ── Gemini ATS Analysis ───────────────────────────────────
async def gemini_ats(resume_text: str, role: str) -> dict:
    model  = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
You are an expert ATS (Applicant Tracking System) and career counselor for the Indian job market.

Target Role: {role}
Resume Text:
---
{resume_text[:4000]}
---

Analyse this resume against the target role and return ONLY a valid JSON object (no markdown):
{{
  "ats_score": <0-100 overall ATS compatibility score>,
  "keyword_score": <0-100 relevant keyword match>,
  "format_score": <0-100 resume structure/format score>,
  "experience_score": <0-100 experience relevance>,
  "present_keywords": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "missing_keywords": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "strengths": ["<strength1>", "<strength2>"],
  "improvements": ["<improvement1>", "<improvement2>", "<improvement3>"],
  "overall_feedback": "<3-4 sentence constructive assessment>",
  "self_intro_draft": "<A 3-sentence self-introduction based on this resume for a {role} interview>"
}}
"""
    response = model.generate_content(prompt)
    raw = response.text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def local_ats(resume_text: str, role: str) -> dict:
    """Rule-based fallback when Gemini unavailable."""
    text  = resume_text.lower()
    score = 0
    present, missing = [], []

    checks = {
        "skills":     ["skills", "technical skills"],
        "experience": ["experience", "internship", "work"],
        "education":  ["education", "degree", "b.tech", "b.e.", "mca"],
        "projects":   ["project", "github"],
        "certifications": ["certification", "certified", "course"],
    }
    for section, kws in checks.items():
        if any(k in text for k in kws):
            score += 20
            present.append(section)
        else:
            missing.append(section)

    return {
        "ats_score":        score,
        "keyword_score":    min(100, score + 5),
        "format_score":     70,
        "experience_score": 60,
        "present_keywords": present,
        "missing_keywords": missing,
        "strengths":        ["Resume provided for analysis"],
        "improvements":     [f"Add missing sections: {', '.join(missing)}"] if missing else ["Good structure!"],
        "overall_feedback": f"Your resume scores {score}/100 against the {role} role. Enable Gemini for deeper analysis.",
        "self_intro_draft": f"I am a motivated professional seeking a {role} role. My resume highlights relevant experience and skills. I am eager to contribute and grow with your organisation."
    }


# ── Endpoints ─────────────────────────────────────────────

@router.post("/analyze", response_model=ATSResponse)
async def analyze_resume(req: ATSRequest):
    resume_id = str(uuid.uuid4())

    # Save raw resume to preptalk_ats → resumes
    r_doc = resume_doc(resume_id, req.resume_text, req.user_id)
    await resumes_col().insert_one(r_doc)

    # AI analysis
    if GEMINI_KEY and req.resume_text.strip():
        try:
            ai_result = await gemini_ats(req.resume_text, req.target_role)
        except Exception:
            ai_result = local_ats(req.resume_text, req.target_role)
    else:
        ai_result = local_ats(req.resume_text, req.target_role)

    # Save ATS result to preptalk_ats → ats_results
    result_doc = ats_result_doc(resume_id, req.target_role, ai_result)
    await ats_results_col().insert_one(result_doc)

    return {"resume_id": resume_id, **ai_result}


@router.get("/history")
async def ats_history(user_id: str = "guest", limit: int = 10):
    """Join resumes with their ATS results."""
    resumes = await resumes_col().find(
        {"user_id": user_id}, {"_id": 0, "raw_text": 0}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)

    results = []
    for r in resumes:
        result = await ats_results_col().find_one(
            {"resume_id": r["resume_id"]}, {"_id": 0}
        )
        results.append({**r, "ats_result": result})

    return {"history": results}


@router.get("/{resume_id}")
async def get_ats_result(resume_id: str):
    result = await ats_results_col().find_one({"resume_id": resume_id}, {"_id": 0})
    if not result:
        return {"error": "ATS result not found"}
    return result
