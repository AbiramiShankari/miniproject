"""
MongoDB document schemas for PrepTalk.
Organised by database domain.
"""

from datetime import datetime


# ════════════════════════════════════════════════
#  DATABASE: preptalk_interviews
# ════════════════════════════════════════════════

def user_doc(user_id: str, name: str, email: str, auth_provider: str = "email") -> dict:
    """User profile stored in MongoDB."""
    return {
        "user_id":       user_id,
        "name":          name,
        "email":         email,
        "auth_provider": auth_provider,
        "created_at":    datetime.utcnow()
    }


def session_doc(session_id: str, role: str, category: str, difficulty: str, user_id: str = "guest") -> dict:
    """One document per mock interview session."""
    return {
        "session_id":   session_id,
        "user_id":      user_id,
        "role":         role,
        "category":     category,        # technical | hr | behavioral | mixed
        "difficulty":   difficulty,      # fresher | intermediate | advanced
        "status":       "active",        # active | completed
        "questions":    [],              # list of question strings
        "total_questions": 0,
        "violations":   0,
        "avg_score":    None,
        "created_at":   datetime.utcnow(),
        "completed_at": None,
    }


def evaluation_doc(session_id: str, question: str, transcript: str, ai_result: dict) -> dict:
    """One document per answered question — stores transcript + full AI analysis."""
    return {
        "session_id":        session_id,
        "question":          question,
        "transcript":        transcript,
        "score":             ai_result.get("score"),
        "clarity_score":     ai_result.get("clarity_score"),
        "confidence_score":  ai_result.get("confidence_score"),
        "relevance_score":   ai_result.get("relevance_score"),
        "filler_words":      ai_result.get("filler_words_found", []),
        "filler_count":      ai_result.get("filler_word_count", 0),
        "overall_feedback":  ai_result.get("overall_feedback"),
        "strengths":         ai_result.get("strengths", []),
        "improvements":      ai_result.get("improvements", []),
        "ideal_answer_hint": ai_result.get("ideal_answer_hint"),
        "created_at":        datetime.utcnow(),
    }


def proctor_doc(session_id: str, event_type: str, details: str) -> dict:
    """One doc per proctoring violation/event."""
    return {
        "session_id": session_id,
        "event_type": event_type,    # tab_switch | face_absent | copy_attempt | window_blur
        "details":    details,
        "created_at": datetime.utcnow(),
    }


def chat_doc(thread_id: str, role: str, content: str) -> dict:
    """One document per chat message in AI Coach."""
    return {
        "thread_id":  thread_id,
        "role":       role,    # user | assistant
        "content":    content,
        "created_at": datetime.utcnow(),
    }


# ════════════════════════════════════════════════
#  DATABASE: preptalk_ats
# ════════════════════════════════════════════════

def resume_doc(resume_id: str, raw_text: str, user_id: str = "guest") -> dict:
    """Stored raw resume text."""
    return {
        "resume_id":  resume_id,
        "user_id":    user_id,
        "raw_text":   raw_text,
        "word_count": len(raw_text.split()),
        "created_at": datetime.utcnow(),
    }


def ats_result_doc(resume_id: str, role: str, ai_result: dict) -> dict:
    """ATS analysis result linked to a resume."""
    return {
        "resume_id":         resume_id,
        "target_role":       role,
        "ats_score":         ai_result.get("ats_score"),
        "keyword_score":     ai_result.get("keyword_score"),
        "format_score":      ai_result.get("format_score"),
        "experience_score":  ai_result.get("experience_score"),
        "missing_keywords":  ai_result.get("missing_keywords", []),
        "present_keywords":  ai_result.get("present_keywords", []),
        "strengths":         ai_result.get("strengths", []),
        "improvements":      ai_result.get("improvements", []),
        "overall_feedback":  ai_result.get("overall_feedback"),
        "self_intro_draft":  ai_result.get("self_intro_draft"),
        "created_at":        datetime.utcnow(),
    }


# ════════════════════════════════════════════════
#  DATABASE: preptalk_practice
# ════════════════════════════════════════════════

def pyq_cache_doc(company: str, questions: list) -> dict:
    """Cached Firecrawl PYQ results — avoids repeat API calls."""
    return {
        "company":   company.lower(),
        "questions": questions,
        "cached_at": datetime.utcnow(),
    }


def aptitude_result_doc(user_id: str, category: str, score: int, total: int, answers: list) -> dict:
    """Aptitude test result."""
    return {
        "user_id":    user_id,
        "category":   category,
        "score":      score,
        "total":      total,
        "percentage": round((score / total) * 100, 1) if total > 0 else 0,
        "answers":    answers,   # list of {question, selected, correct}
        "created_at": datetime.utcnow(),
    }
