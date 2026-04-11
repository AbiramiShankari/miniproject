# PrepTalk – Full Stack Interview Prep Platform

## 🚀 Quick Start

### 1. Backend (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env and add your API keys:
#   GOOGLE_API_KEY=...    (from https://aistudio.google.com/app/apikey)
#   FIRECRAWL_API_KEY=... (from https://www.firecrawl.dev/)

# Start the API server
uvicorn main:app --reload --port 8000
```

> API docs: http://localhost:8000/docs

### 2. Frontend

Open `frontend/pages/dashboard.html` in **Chrome** (required for Web Speech API).

---

## 🗂️ Project Structure

```
PrepTalk/
├── backend/
│   ├── main.py                  ← FastAPI app entry point
│   ├── .env                     ← API keys (do not commit)
│   ├── requirements.txt
│   ├── routes/
│   │   ├── speech.py            ← 🧠 AI speech analysis + proctor event log
│   │   ├── communication.py     ← Communication module evaluator
│   │   └── practice.py          ← Firecrawl PYQ crawler endpoint
│   ├── crawler/
│   │   └── firecrawl_api.py     ← Firecrawl integration
│   └── database/
│       ├── database.py          ← SQLAlchemy + SQLite
│       └── models.py            ← DB models
│
└── frontend/
    ├── login.html               ← Auth entry point
    ├── static/
    │   └── js/nav.js            ← Shared sidebar nav (auto-injected)
    └── pages/
        ├── dashboard.html       ← Home + stats + progress chart
        ├── live_mock.html       ← 🎙️ Live mock interview (speech AI + proctor)
        ├── comm_hub.html        ← 🗣️ Communication training hub
        ├── pyq_bank.html        ← 🏢 Company PYQ bank (Firecrawl)
        ├── aptitude.html        ← 🧠 Aptitude practice
        ├── role.html            ← 🎯 Role & interview config
        ├── feedback.html        ← 📊 Session feedback report
        ├── ai_coach.html        ← 🤖 AI Coach chatbot
        └── resume_ats.html      ← 📄 Resume ATS checker
```

---

## ✨ Key Features

| Feature | How it works |
|---|---|
| **Live Speech-to-Text** | Browser Web Speech API — transcribes voice in real-time |
| **AI Speech Analysis** | Gemini 1.5 Flash — scores clarity, confidence, relevance, detects filler words |
| **AI Question Generation** | Gemini generates role-specific questions per session |
| **Proctor AI** | Tab-switch detection, window blur tracking, copy/paste prevention, brightness-based face detection |
| **Firecrawl PYQ Crawler** | Crawls GeeksForGeeks & similar sites for company interview questions |
| **Shared Navigation** | `nav.js` auto-injects sidebar on every page |
| **Session Persistence** | localStorage + sessionStorage track scores across pages |
| **Communication Hub** | 5 modules (Self-Intro, GD, HR, Tech HR, Email) with voice input |
| **Feedback Report** | Radar chart, bar analysis, violation log, strengths/improvements |
