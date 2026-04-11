"""
routes/ai_coach.py  — preptalk_interviews → chat_history
Gemini-powered chat coach. Saves every message to MongoDB.

Endpoints:
  POST /api/coach/chat        → send message, get Gemini reply, persist both
  GET  /api/coach/{thread_id} → full conversation history
"""

import os, uuid, json
from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from backend.database.database import chat_history_col
from backend.database.models import chat_doc

load_dotenv()
router = APIRouter()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """You are PrepTalk AI Coach — a friendly, expert interview preparation assistant
specialised for Indian engineering graduates and professionals.
You give concise, practical advice on:
- Technical interview preparation (DSA, OS, DBMS, System Design)
- Behavioural questions (STAR method)
- HR rounds, salary negotiation, GD tips
- Self-introduction crafting
- Resume feedback
Keep responses focused, structured, and under 200 words unless detail is specifically requested."""


class ChatRequest(BaseModel):
    thread_id: str = ""     # empty = new conversation
    message:   str
    user_id:   str = "guest"


@router.post("/chat")
async def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())

    # Save user message
    await chat_history_col().insert_one(
        chat_doc(thread_id, "user", req.message)
    )

    if GEMINI_KEY:
        try:
            # Fetch recent history for context
            history = await chat_history_col().find(
                {"thread_id": thread_id}, {"_id": 0, "role": 1, "content": 1}
            ).sort("created_at", 1).limit(20).to_list(length=20)

            # Build Gemini conversation
            model = genai.GenerativeModel("gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT)

            gemini_history = [
                {"role": "user" if m["role"] == "user" else "model",
                 "parts": [m["content"]]}
                for m in history[:-1]   # exclude the just-saved msg
            ]

            chat_session = model.start_chat(history=gemini_history)
            response     = chat_session.send_message(req.message)
            reply        = response.text.strip()

        except Exception as e:
            reply = f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)[:80]})"
    else:
        reply = ("Gemini API key not configured. Add GOOGLE_API_KEY to your .env file "
                 "to enable full AI Coach functionality.")

    # Save assistant reply
    await chat_history_col().insert_one(
        chat_doc(thread_id, "assistant", reply)
    )

    return {"thread_id": thread_id, "reply": reply}


@router.get("/{thread_id}")
async def get_history(thread_id: str):
    msgs = await chat_history_col().find(
        {"thread_id": thread_id}, {"_id": 0, "role": 1, "content": 1, "created_at": 1}
    ).sort("created_at", 1).to_list(length=100)

    return {"thread_id": thread_id, "messages": msgs}
