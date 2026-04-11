"""
routes/speech.py
AI speech evaluation (Gemini), proctor event logging,
question generation — all results persisted to preptalk_interviews DB.

Endpoints:
  POST /api/speech/analyze          → AI evaluation of spoken answer + save to evaluations
  POST /api/speech/proctor/log      → save proctoring violation event
  POST /api/speech/questions/generate → quick question generation (no session)
"""

import os, json
from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from backend.database.database import evaluations_col, proctor_logs_col
from backend.database.models import evaluation_doc, proctor_doc

load_dotenv()
router = APIRouter()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "right", "so", "okay", "actually", "kind of", "sort of", "hmm"
]


# ── Schemas ───────────────────────────────────────────────
class SpeechEvalRequest(BaseModel):
    session_id: str = "standalone"
    question:   str
    transcript: str
    category:   str = "interview"

class ProctorEvent(BaseModel):
    session_id: str
    event_type: str     # tab_switch | face_absent | copy_attempt | window_blur
    timestamp:  str
    details:    str = ""

class QuestionRequest(BaseModel):
    role:       str
    experience: str = "fresher"
    category:   str = "mixed"


# ── Helpers ───────────────────────────────────────────────
def count_fillers(text: str) -> list[str]:
    found = []
    lower = text.lower()
    for fw in FILLER_WORDS:
        if f" {fw} " in lower or lower.startswith(fw+" ") or lower.endswith(" "+fw):
            if fw not in found:
                found.append(fw)
    return found


def local_score(transcript: str, category: str) -> dict:
    """Rule-based fallback when Gemini is unavailable."""
    wc      = len(transcript.split())
    fillers = count_fillers(transcript)
    score   = min(10, max(1, (wc // 15) + max(0, 5 - len(fillers))))
    return {
        "score":             score,
        "clarity_score":     max(1, score),
        "confidence_score":  max(1, score - 1),
        "relevance_score":   max(1, score),
        "filler_word_count": len(fillers),
        "filler_words_found": fillers,
        "overall_feedback":  (
            "Your answer is too brief — try to elaborate with examples." if wc < 25
            else "Decent response. Use the STAR method to add structure and depth."
        ),
        "strengths":         ["Attempted the question", "Adequate vocabulary"],
        "improvements":      [
            f"Reduce filler words: {', '.join(fillers[:3])}" if fillers else "Minimise hesitations",
            "Add specific metrics or project outcomes",
            "Structure with: Situation → Task → Action → Result"
        ],
        "ideal_answer_hint": "Lead with the context, describe your specific action, and end with a measurable result."
    }


async def gemini_eval(question: str, transcript: str, category: str, fillers: list) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
You are an expert interview coach for Indian engineering freshers/professionals.

Interview Question: "{question}"
Category: {category}
Candidate's spoken answer (transcribed): "{transcript}"
Detected filler words: {fillers}

Evaluate the answer. Return ONLY a valid JSON object (no markdown, no extra text):
{{
  "score": <1-10 overall>,
  "clarity_score": <1-10>,
  "confidence_score": <1-10>,
  "relevance_score": <1-10>,
  "overall_feedback": "<2-3 sentences of constructive feedback>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
  "ideal_answer_hint": "<1-2 sentences on what a strong answer should include>"
}}
"""
    response = model.generate_content(prompt)
    raw = response.text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


# ── Endpoints ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_speech(req: SpeechEvalRequest):
    fillers = count_fillers(req.transcript)

    if GEMINI_KEY and req.transcript.strip():
        try:
            result = await gemini_eval(req.question, req.transcript, req.category, fillers)
        except Exception:
            result = local_score(req.transcript, req.category)
    else:
        result = local_score(req.transcript, req.category)

    result["filler_word_count"]  = len(fillers)
    result["filler_words_found"] = fillers

    # Persist to preptalk_interviews → evaluations
    doc = evaluation_doc(req.session_id, req.question, req.transcript, result)
    await evaluations_col().insert_one(doc)

    return result


@router.post("/proctor/log")
async def log_proctor_event(event: ProctorEvent):
    doc = proctor_doc(event.session_id, event.event_type, event.details)
    await proctor_logs_col().insert_one(doc)

    # Increment violation count on session
    from backend.database.database import sessions_col
    await sessions_col().update_one(
        {"session_id": event.session_id},
        {"$inc": {"violations": 1}}
    )

    severity = "warn" if event.event_type in ["tab_switch", "multiple_faces"] else "info"
    return {"status": "logged", "severity": severity}


@router.post("/questions/generate")
async def generate_questions(req: QuestionRequest):
    if not GEMINI_KEY:
        return {"questions": [
            f"Tell me about yourself and your interest in {req.role}.",
            "Describe a challenging project you worked on.",
            "How do you handle pressure and tight deadlines?",
            f"What technical skills do you bring to {req.role}?",
            "Where do you see yourself in 3 years?"
        ]}
    try:
        model  = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""Generate exactly 5 {req.category} interview questions for a {req.experience} applying for {req.role}.
Return ONLY a JSON array of 5 strings, no markdown:
["q1","q2","q3","q4","q5"]"""
        response = model.generate_content(prompt)
        raw      = response.text.strip().strip("```json").strip("```").strip()
        return {"questions": json.loads(raw)}
    except Exception as e:
        return {"questions": [
            f"Tell me about yourself and your interest in {req.role}.",
            "Describe a project you're most proud of.",
            "How do you handle working under pressure?",
            f"What are your key strengths for a {req.role} role?",
            "Where do you see yourself in 3 years?"
        ]}
