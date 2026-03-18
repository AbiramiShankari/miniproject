from fastapi import FastAPI
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI()

# -----------------------------
# Test Route
# -----------------------------
@app.get("/")
def home():
    return {"message": "PrepTalk Backend is Running 🚀"}

# -----------------------------
# Health Check API
# -----------------------------
@app.get("/health")
def health_check():
    return {"status": "Server is healthy"}

# -----------------------------
# Sample Interview Question API
# -----------------------------
@app.get("/question")
def get_question():
    return {
        "question": "Tell me about a challenging project you worked on."
    }

# -----------------------------
# Request Model
# -----------------------------
class Answer(BaseModel):
    answer: str

# -----------------------------
# Evaluate Answer API
# -----------------------------
@app.post("/evaluate")
def evaluate_answer(data: Answer):

    answer_text = data.answer

    # Dummy evaluation logic
    clarity_score = 7
    confidence_score = 6
    structure_score = 8
    technical_score = 7

    return {
        "answer_received": answer_text,
        "evaluation": {
            "clarity": clarity_score,
            "confidence": confidence_score,
            "structure": structure_score,
            "technical_depth": technical_score
        },
        "suggestions": [
            "Reduce filler words",
            "Use structured answers (STAR method)",
            "Explain results clearly"
        ]
    }