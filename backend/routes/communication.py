"""
routes/communication.py
Evaluates communication practice responses using Gemini.
Results are stored as standalone evaluations (session_id = "comm_<uuid>")
in preptalk_interviews → evaluations.
"""

import os, json, uuid
from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from backend.database.database import evaluations_col
from backend.database.models import evaluation_doc
from backend.routes.speech import count_fillers, local_score

load_dotenv()
router = APIRouter()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


class CommEvalRequest(BaseModel):
    category:      str          # self | gd | hr | tech | email
    question:      str = ""     # optional prompt/topic
    response_text: str
    user_id:       str = "guest"


@router.post("/evaluate")
async def evaluate_communication(req: CommEvalRequest):
    session_id = f"comm_{uuid.uuid4()}"
    question   = req.question or f"{req.category.upper()} Communication Practice"
    fillers    = count_fillers(req.response_text)

    if GEMINI_KEY and req.response_text.strip():
        try:
            model  = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
You are an expert communication coach for Indian professionals.

Practice Category: {req.category}
Topic/Question: {question}
Candidate's response: "{req.response_text}"
Filler words detected: {fillers}

Evaluate the communication and return ONLY a valid JSON (no markdown):
{{
  "score": <1-10>,
  "clarity_score": <1-10>,
  "confidence_score": <1-10>,
  "relevance_score": <1-10>,
  "filler_word_count": {len(fillers)},
  "filler_words_found": {json.dumps(fillers)},
  "overall_feedback": "<2-3 constructive sentences>",
  "strengths": ["<s1>", "<s2>"],
  "improvements": ["<i1>", "<i2>", "<i3>"],
  "ideal_answer_hint": "<1-2 sentences on what a great response looks like>"
}}
"""
            response = model.generate_content(prompt)
            raw      = response.text.strip().strip("```json").strip("```").strip()
            result   = json.loads(raw)
            result["filler_word_count"]  = len(fillers)
            result["filler_words_found"] = fillers
        except Exception:
            result = local_score(req.response_text, req.category)
    else:
        result = local_score(req.response_text, req.category)

    # Persist as an evaluation record in preptalk_interviews
    doc = evaluation_doc(session_id, question, req.response_text, result)
    await evaluations_col().insert_one(doc)

    return result
