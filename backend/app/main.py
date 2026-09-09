from __future__ import annotations

import os, re, uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import fitz
from fastapi import FastAPI, Depends, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from openai import OpenAI
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campus_hub.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Student")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(255), default="General")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(255), default="General")
    text: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
app = FastAPI(title="Campus Hub API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def token_for(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db_session)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
        if not user: raise HTTPException(401, "Invalid account")
        return user
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired session")

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def fallback_summary(text: str, max_sentences: int = 12) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))
    chosen = [s for s in sentences if len(s) > 35][:max_sentences]
    return "\n• " + "\n• ".join(chosen) if chosen else clean_text(text)[:2400]

def ai_answer(prompt: str, context: str = "") -> str:
    if not OPENAI_API_KEY:
        return fallback_summary(context or prompt)
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": "You are Smith, a concise academic assistant. Be clear, practical, accurate, and student-friendly. Use supplied academic context when available."},
            {"role": "user", "content": f"Context:\n{context[:120000]}\n\nRequest:\n{prompt}"}
        ]
    )
    return response.output_text.strip()

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
def health(): return {"ok": True, "service": "campus-hub-api"}

@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(db_session)):
    if db.query(User).filter(User.email == data.email.lower()).first(): raise HTTPException(409, "Email already registered")
    user = User(name=data.name.strip() or "Student", email=data.email.lower(), password_hash=pwd_context.hash(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": token_for(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not pwd_context.verify(data.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
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
    row = Assignment(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.post("/notes/upload")
async def upload_note(file: UploadFile = File(...), course: str = "General", user: User = Depends(current_user), db: Session = Depends(db_session)):
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"): raise HTTPException(400, "Please upload a PDF")
    raw = await file.read()
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)
    except Exception: raise HTTPException(400, "This PDF could not be read")
    text = clean_text(text)
    if len(text) < 80: raise HTTPException(422, "This PDF has little extractable text")
    title = os.path.splitext(file.filename or "Lecture notes")[0]
    summary = ai_answer("Summarize these lecture notes into exam-ready points. Include definitions, key ideas, and important examples.", text)
    row = Note(user_id=user.id, title=title, course=course, text=text, summary=summary); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "title": row.title, "course": row.course, "summary": row.summary}

@app.get("/notes")
def notes(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "summary": r.summary, "created_at": r.created_at} for r in rows]

@app.post("/assistant/chat")
def assistant_chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    context_parts = []
    assignments = db.query(Assignment).filter(Assignment.user_id == user.id).order_by(Assignment.due_at.asc()).limit(12).all()
    if assignments: context_parts.append("Assignments:\n" + "\n".join(f"- {a.title} | {a.course} | due {a.due_at} | {a.progress}% | {a.status}" for a in assignments))
    if data.documentId:
        note = db.query(Note).filter(Note.id == data.documentId, Note.user_id == user.id).first()
        if note: context_parts.append(f"Selected note: {note.title}\n{note.text}")
    else:
        recent = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).limit(3).all()
        for n in recent: context_parts.append(f"Recent note: {n.title}\n{n.summary or n.text[:5000]}")
    mode_instruction = {"tutor":"Teach step by step, then ask one short check question.","exam":"Respond like an exam revision coach. Focus on likely testable points and concise answers.","planner":"Create a realistic prioritized academic plan with times only when the user supplies or context contains them.","focus":"Keep the answer extremely short and tell the student the next action.","normal":"Answer directly and clearly."}.get(data.mode, "Answer directly and clearly.")
    prompt = f"Mode instruction: {mode_instruction}\nStudent name: {user.name}\nStudent request: {data.message}"
    return {"reply": ai_answer(prompt, "\n\n".join(context_parts))}
