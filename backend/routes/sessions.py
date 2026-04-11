"""
routes/sessions.py
Interview session lifecycle with RESUME-FIRST personalized question generation.

  POST /api/sessions/start-from-resume  → parse resume + generate personalized Qs
  POST /api/sessions/start              → generic start (fallback)
  POST /api/sessions/complete           → mark done, compute avg score
  GET  /api/sessions                    → list sessions (latest first)
  GET  /api/sessions/{session_id}       → full detail + evaluations
"""

import os, json, uuid
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from backend.database.database import sessions_col, evaluations_col
from backend.database.models import session_doc

load_dotenv()
router = APIRouter()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


# ── Schemas ────────────────────────────────────────────────
class ResumeSessionRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    difficulty:  str = "fresher"
    category:    str = "mixed"
    user_id:     str = "guest"
    num_questions: int = 7

class StartSessionRequest(BaseModel):
    role:       str
    category:   str = "mixed"
    difficulty: str = "fresher"
    user_id:    str = "guest"

class CompleteSessionRequest(BaseModel):
    session_id: str


# ── Resume Parsing + Personalized Q Generation ─────────────
async def generate_from_resume(resume_text: str, role: str,
                                difficulty: str, category: str,
                                num_q: int) -> tuple[list[str], dict]:
    """
    Returns (questions_list, resume_profile_dict)
    All questions are derived from the actual resume content.
    """
    if not GEMINI_KEY:
        return _fallback_questions(role), {}

    model = genai.GenerativeModel("gemini-2.5-flash")

    # Step 1: Parse the resume to extract profile
    parse_prompt = f"""
You are an expert resume analyser. Carefully read this resume and extract key information.

Resume:
---
{resume_text[:5000]}
---

Return ONLY a valid JSON object (no markdown):
{{
  "name": "<candidate name or 'Candidate'>",
  "current_status": "<student/fresher/experienced>",
  "skills": ["<skill1>", "<skill2>", "<skill3>"],
  "projects": [
    {{"name": "<project name>", "tech": "<main tech used>", "description": "<1 sentence>"}}
  ],
  "internships": [
    {{"company": "<company>", "role": "<role>", "work": "<what they did>"}}
  ],
  "certifications": ["<cert1>"],
  "education": {{"degree": "<degree>", "college": "<college>", "year": "<graduation year>"}},
  "key_strengths": ["<strength1>", "<strength2>"]
}}
"""
    profile = {}
    try:
        parse_resp = model.generate_content(parse_prompt)
        raw = parse_resp.text.strip().strip("```json").strip("```").strip()
        profile = json.loads(raw)
    except Exception:
        profile = {}

    # Step 2: Generate interview questions FROM the resume profile
    q_prompt = f"""
You are Priya — a senior interviewer at a tech company. You are interviewing a candidate for {role}.
Interview difficulty: {difficulty}. Interview type: {category}.

This is what you know about the candidate FROM their resume:
{json.dumps(profile, indent=2) if profile else resume_text[:2000]}

Generate exactly {num_q} interview questions that:
1. Reference SPECIFIC projects, skills, technologies, or experiences from THEIR resume
2. Are detailed and probing — not generic
3. Sound like a real interviewer who has READ the resume
4. Mix technical depth, problem-solving, and behavioral angles
5. Progressively get harder

Format: Return ONLY a JSON array of {num_q} strings, no markdown, no numbering:
["question1", "question2", ...]

Examples of GOOD personalized questions (use the actual resume data):
- "I noticed you built [project name] using [their tech]. Walk me through the most challenging part."
- "You've listed [their skill] on your resume — give me a real scenario where you used it."
- "Your internship at [their company] involved [their work]. What would you do differently now?"
"""
    try:
        q_resp = model.generate_content(q_prompt)
        raw = q_resp.text.strip().strip("```json").strip("```").strip()
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) >= num_q:
            return questions[:num_q], profile
    except Exception:
        pass

    return _fallback_questions(role), profile


def _fallback_questions(role: str) -> list[str]:
    return [
        f"Tell me about yourself and your interest in {role}.",
        "Walk me through your most significant project. What was your role?",
        "Describe a technical challenge you faced and how you solved it.",
        f"Which of your skills do you feel is most relevant for {role}? Give a real example.",
        "Tell me about a time you had to learn something quickly under pressure.",
        "How do you approach debugging a problem you've never seen before?",
        "Where do you see yourself in 3 years?"
    ]


# ── Generic start (all fallback questions) ─────────────────
async def _generic_questions(role: str, category: str, difficulty: str) -> list[str]:
    if not GEMINI_KEY:
        return _fallback_questions(role)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""Generate exactly 5 {category} interview questions for a {difficulty} candidate
applying for {role}. Return ONLY a JSON array of 5 strings, no markdown:
["q1","q2","q3","q4","q5"]"""
        response = model.generate_content(prompt)
        raw = response.text.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception:
        return _fallback_questions(role)


# ── Endpoints ──────────────────────────────────────────────

@router.post("/start-from-resume")
async def start_from_resume(req: ResumeSessionRequest):
    """
    PRIMARY endpoint — parses resume with Gemini, generates
    personalized questions rooted in the candidate's actual experience.
    """
    session_id = str(uuid.uuid4())
    questions, profile = await generate_from_resume(
        req.resume_text, req.target_role, req.difficulty, req.category, req.num_questions
    )

    doc = session_doc(session_id, req.target_role, req.category, req.difficulty, req.user_id)
    doc["questions"]       = questions
    doc["total_questions"] = len(questions)
    doc["resume_profile"]  = profile   # store parsed profile for later reference

    await sessions_col().insert_one(doc)

    return {
        "status":     "started",
        "session_id": session_id,
        "questions":  questions,
        "profile":    profile,
        "role":       req.target_role,
        "category":   req.category,
        "difficulty": req.difficulty,
    }


@router.post("/start")
async def start_session(req: StartSessionRequest):
    """Fallback — generic questions when no resume provided."""
    session_id = str(uuid.uuid4())
    questions  = await _generic_questions(req.role, req.category, req.difficulty)

    doc = session_doc(session_id, req.role, req.category, req.difficulty, req.user_id)
    doc["questions"]       = questions
    doc["total_questions"] = len(questions)

    await sessions_col().insert_one(doc)

    return {
        "status": "started", "session_id": session_id,
        "questions": questions, "role": req.role,
    }


@router.post("/complete")
async def complete_session(req: CompleteSessionRequest):
    evals  = await evaluations_col().find(
        {"session_id": req.session_id}, {"score": 1}
    ).to_list(length=100)

    scores = [e["score"] for e in evals if e.get("score") is not None]
    avg    = round(sum(scores) / len(scores), 1) if scores else None

    await sessions_col().update_one(
        {"session_id": req.session_id},
        {"$set": {"status": "completed", "avg_score": avg, "completed_at": datetime.utcnow()}}
    )
    return {"status": "completed", "session_id": req.session_id, "avg_score": avg}


@router.get("")
async def list_sessions(user_id: str = "guest", limit: int = 20):
    cursor = sessions_col().find(
        {"user_id": user_id}, {"_id": 0, "resume_profile": 0}
    ).sort("created_at", -1).limit(limit)
    return {"sessions": await cursor.to_list(length=limit)}


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = await sessions_col().find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        return {"error": "Session not found"}
    evals = await evaluations_col().find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(length=100)
    return {"session": session, "evaluations": evals}
