from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import fitz
from fastapi import FastAPI, Depends, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campus_hub.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "campus_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Student")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "campus_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(255), default="General")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)

class Note(Base):
    __tablename__ = "campus_notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(255), default="General")
    text: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
app = FastAPI(title="Campus Hub API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def token_for(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db_session)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
        if not user:
            raise HTTPException(401, "Invalid account")
        return user
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired session")

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def fallback_summary(text: str, max_sentences: int = 12) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))
    chosen = [s for s in sentences if len(s) > 35][:max_sentences]
    return "\n• " + "\n• ".join(chosen) if chosen else clean_text(text)[:2400]

def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    request = urllib.request.Request(
        f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"[smith] Gemini API error {exc.code}: {body[:1200]}")
        raise RuntimeError("Gemini is temporarily unavailable") from exc
    except Exception as exc:
        print(f"[smith] Gemini request failed: {exc}")
        raise RuntimeError("Gemini is temporarily unavailable") from exc

    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no response")
    parts = candidates[0].get("content", {}).get("parts", [])
    reply = "".join(part.get("text", "") for part in parts).strip()
    if not reply:
        raise RuntimeError("Gemini returned an empty response")
    return reply

def ai_answer(prompt: str, context: str = "") -> str:
    if not GEMINI_API_KEY:
        return fallback_summary(context or prompt)

    combined = (
        "You are Smith, Campus Hub's academic assistant. Be concise, accurate, practical, and student-friendly. "
        "Use the supplied academic context when available. Never invent assignment dates, course details, or note content. "
        "If context does not contain an answer, say so clearly.\n\n"
        f"Academic context:\n{context[:120000]}\n\n"
        f"Student request:\n{prompt}"
    )
    try:
        return call_gemini(combined)
    except RuntimeError:
        return fallback_summary(context or prompt)

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class AssignmentIn(BaseModel):
    title: str
    course: str = "General"
    due_at: Optional[datetime] = None
    progress: int = 0
    status: str = "pending"

class ChatIn(BaseModel):
    message: str
    mode: str = "normal"
    documentId: Optional[str] = None

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "campus-hub-api",
        "version": "1.1.0",
        "ai_provider": "gemini" if GEMINI_API_KEY else "fallback",
        "database": "postgres" if DATABASE_URL.startswith("postgres") else "sqlite",
    }

@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(db_session)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name.strip() or "Student", email=data.email.lower(), password_hash=pwd_context.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": token_for(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": token_for(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email}

@app.get("/assignments")
def list_assignments(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Assignment).filter(Assignment.user_id == user.id).order_by(Assignment.due_at.asc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "due_at": r.due_at, "progress": r.progress, "status": r.status} for r in rows]

@app.post("/assignments")
def add_assignment(data: AssignmentIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Assignment(user_id=user.id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.post("/notes/upload")
async def upload_note(file: UploadFile = File(...), course: str = "General", user: User = Depends(current_user), db: Session = Depends(db_session)):
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF")
    raw = await file.read()
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)
    except Exception:
        raise HTTPException(400, "This PDF could not be read")
    text = clean_text(text)
    if len(text) < 80:
        raise HTTPException(422, "This PDF has little extractable text")
    title = os.path.splitext(file.filename or "Lecture notes")[0]
    summary = ai_answer(
        "Summarize these lecture notes into exam-ready points. Include definitions, key ideas, important examples, and a short final revision checklist.",
        text,
    )
    row = Note(user_id=user.id, title=title, course=course, text=text, summary=summary)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "title": row.title, "course": row.course, "summary": row.summary}

@app.get("/notes")
def notes(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "summary": r.summary, "created_at": r.created_at} for r in rows]

@app.post("/assistant/chat")
def assistant_chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    context_parts = []
    assignments = db.query(Assignment).filter(Assignment.user_id == user.id).order_by(Assignment.due_at.asc()).limit(12).all()
    if assignments:
        context_parts.append(
            "Assignments:\n" + "\n".join(
                f"- {a.title} | {a.course} | due {a.due_at} | {a.progress}% | {a.status}" for a in assignments
            )
        )
    if data.documentId:
        note = db.query(Note).filter(Note.id == data.documentId, Note.user_id == user.id).first()
        if note:
            context_parts.append(f"Selected note: {note.title}\n{note.text}")
    else:
        recent = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).limit(3).all()
        for n in recent:
            context_parts.append(f"Recent note: {n.title}\n{n.summary or n.text[:5000]}")

    mode_instruction = {
        "tutor": "Teach step by step, then ask one short check question.",
        "exam": "Respond like an exam revision coach. Focus on likely testable points and concise answers.",
        "planner": "Create a realistic prioritized academic plan with times only when the user supplies or context contains them.",
        "focus": "Keep the answer extremely short and tell the student the next action.",
        "normal": "Answer directly and clearly.",
    }.get(data.mode, "Answer directly and clearly.")
    prompt = f"Mode instruction: {mode_instruction}\nStudent name: {user.name}\nStudent request: {data.message}"
    return {"reply": ai_answer(prompt, "\n\n".join(context_parts))}
