"""
routes/auth.py
Handles User Registration, Login, and MongoDB user creation.

Endpoints:
  POST /api/auth/google   → Login or register via Google
  POST /api/auth/register → Email/Password signup
  POST /api/auth/login    → Email/Password signin
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.database import get_client
from backend.database.models import user_doc

router = APIRouter()

# Helper to get users collection
def users_col():
    return get_client()["preptalk_interviews"]["users"]


class AuthGoogleRequest(BaseModel):
    name:  str
    email: str

class AuthBaseRequest(BaseModel):
    name:  str = ""
    email: str
    password: str


@router.post("/google")
async def auth_google(req: AuthGoogleRequest):
    """Mock Google Auth that ensures user exists in MongoDB"""
    user = await users_col().find_one({"email": req.email})
    if not user:
        user_id = str(uuid.uuid4())
        doc = user_doc(user_id, req.name, req.email, "google")
        await users_col().insert_one(doc)
        user = doc
    
    return {
        "status": "success", 
        "user": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


@router.post("/register")
async def auth_register(req: AuthBaseRequest):
    if await users_col().find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_id = str(uuid.uuid4())
    doc = user_doc(user_id, req.name, req.email, "email")
    # In a real app we would hash the password here, mock stores it
    doc["password"] = req.password
    
    await users_col().insert_one(doc)
    return {
        "status": "success",
        "user": {
            "user_id": user_id,
            "name": req.name,
            "email": req.email
        }
    }


@router.post("/login")
async def auth_login(req: AuthBaseRequest):
    user = await users_col().find_one({"email": req.email, "password": req.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return {
        "status": "success",
        "user": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"]
        }
    }
