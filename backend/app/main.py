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
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campus_hub.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

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
    university: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    programme: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    semester: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
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

class TimetableEntry(Base):
    __tablename__ = "campus_timetable"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    course: Mapped[str] = mapped_column(String(255))
    lecturer: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[str] = mapped_column(String(5))
    end_time: Mapped[str] = mapped_column(String(5))

class Exam(Base):
    __tablename__ = "campus_exams"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    course: Mapped[str] = mapped_column(String(255))
    exam_at: Mapped[datetime] = mapped_column(DateTime)
    room: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

class Attendance(Base):
    __tablename__ = "campus_attendance"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    course: Mapped[str] = mapped_column(String(255))
    attended: Mapped[bool] = mapped_column(Boolean, default=True)
    class_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Grade(Base):
    __tablename__ = "campus_grades"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    course: Mapped[str] = mapped_column(String(255))
    credits: Mapped[float] = mapped_column(Float, default=3.0)
    grade_point: Mapped[float] = mapped_column(Float)
    semester: Mapped[str] = mapped_column(String(80), default="Current")

Base.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
app = FastAPI(title="Campus Hub API", version="1.2.0")
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
    request_body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}
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
        "Use supplied academic context. Never invent class times, assignment dates, exam dates, grades, attendance or note content. "
        "If the data does not answer something, say so clearly.\n\n"
        f"Academic context:\n{context[:120000]}\n\nStudent request:\n{prompt}"
    )
    try:
        return call_gemini(combined)
    except RuntimeError:
        return fallback_summary(context or prompt)

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class ProfileIn(BaseModel):
    name: Optional[str] = None
    university: Optional[str] = None
    programme: Optional[str] = None
    semester: Optional[str] = None
class AssignmentIn(BaseModel):
    title: str
    course: str = "General"
    due_at: Optional[datetime] = None
    progress: int = Field(default=0, ge=0, le=100)
    status: str = "pending"
class TimetableIn(BaseModel):
    course: str
    lecturer: Optional[str] = None
    room: Optional[str] = None
    weekday: int = Field(ge=0, le=6)
    start_time: str
    end_time: str
class ExamIn(BaseModel):
    course: str
    exam_at: datetime
    room: Optional[str] = None
class AttendanceIn(BaseModel):
    course: str
    attended: bool = True
    class_date: datetime = Field(default_factory=datetime.utcnow)
class GradeIn(BaseModel):
    course: str
    credits: float = Field(default=3.0, gt=0)
    grade_point: float = Field(ge=0, le=5)
    semester: str = "Current"
class ChatIn(BaseModel):
    message: str
    mode: str = "normal"
    documentId: Optional[str] = None

@app.get("/")
def root():
    return {"service": "Campus Hub API", "status": "online", "docs": "/docs"}

@app.get("/health")
def health():
    return {"ok": True, "service": "campus-hub-api", "version": "1.2.0", "ai_provider": "gemini" if GEMINI_API_KEY else "fallback", "database": "postgres" if DATABASE_URL.startswith("postgres") else "sqlite"}

@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(db_session)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name.strip() or "Student", email=data.email.lower(), password_hash=pwd_context.hash(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": token_for(user.id), "user": profile_dict(user)}

@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": token_for(user.id), "user": profile_dict(user)}

def profile_dict(user: User):
    return {"id": user.id, "name": user.name, "email": user.email, "university": user.university, "programme": user.programme, "semester": user.semester}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return profile_dict(user)

@app.patch("/me")
def update_me(data: ProfileIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return profile_dict(user)

@app.get("/assignments")
def list_assignments(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Assignment).filter(Assignment.user_id == user.id).order_by(Assignment.due_at.asc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "due_at": r.due_at, "progress": r.progress, "status": r.status} for r in rows]

@app.post("/assignments")
def add_assignment(data: AssignmentIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Assignment(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.get("/timetable")
def get_timetable(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id).order_by(TimetableEntry.weekday, TimetableEntry.start_time).all()
    return [{"id": r.id, "course": r.course, "lecturer": r.lecturer, "room": r.room, "weekday": r.weekday, "start_time": r.start_time, "end_time": r.end_time} for r in rows]

@app.post("/timetable")
def add_timetable(data: TimetableIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    if not re.fullmatch(r"\d{2}:\d{2}", data.start_time) or not re.fullmatch(r"\d{2}:\d{2}", data.end_time):
        raise HTTPException(422, "Times must use HH:MM format")
    row = TimetableEntry(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.get("/exams")
def get_exams(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_at).all()
    return [{"id": r.id, "course": r.course, "exam_at": r.exam_at, "room": r.room} for r in rows]

@app.post("/exams")
def add_exam(data: ExamIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Exam(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.get("/attendance")
def attendance_summary(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Attendance).filter(Attendance.user_id == user.id).all()
    grouped = {}
    for r in rows:
        item = grouped.setdefault(r.course, {"course": r.course, "attended": 0, "total": 0})
        item["total"] += 1
        item["attended"] += 1 if r.attended else 0
    return [{**v, "percentage": round((v["attended"] / v["total"]) * 100, 1) if v["total"] else 0} for v in grouped.values()]

@app.post("/attendance")
def add_attendance(data: AttendanceIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Attendance(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.get("/grades")
def grades(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Grade).filter(Grade.user_id == user.id).all()
    credits = sum(r.credits for r in rows)
    gpa = round(sum(r.credits * r.grade_point for r in rows) / credits, 2) if credits else None
    return {"gpa": gpa, "courses": [{"id": r.id, "course": r.course, "credits": r.credits, "grade_point": r.grade_point, "semester": r.semester} for r in rows]}

@app.post("/grades")
def add_grade(data: GradeIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Grade(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}

@app.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(db_session)):
    now = datetime.now()
    weekday = now.weekday()
    today = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id, TimetableEntry.weekday == weekday).order_by(TimetableEntry.start_time).all()
    upcoming_assignments = db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.status != "completed").order_by(Assignment.due_at.asc()).limit(5).all()
    next_exams = db.query(Exam).filter(Exam.user_id == user.id, Exam.exam_at >= now).order_by(Exam.exam_at).limit(3).all()
    grade_rows = db.query(Grade).filter(Grade.user_id == user.id).all()
    credits = sum(r.credits for r in grade_rows)
    gpa = round(sum(r.credits * r.grade_point for r in grade_rows) / credits, 2) if credits else None
    return {
        "profile": profile_dict(user),
        "classes": [{"id": r.id, "course": r.course, "room": r.room, "start_time": r.start_time, "end_time": r.end_time} for r in today],
        "assignments": [{"id": r.id, "title": r.title, "course": r.course, "due_at": r.due_at, "progress": r.progress, "status": r.status} for r in upcoming_assignments],
        "exams": [{"id": r.id, "course": r.course, "exam_at": r.exam_at, "room": r.room} for r in next_exams],
        "gpa": gpa,
    }

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
    summary = ai_answer("Summarize these lecture notes into exam-ready points. Include definitions, key ideas, important examples, likely exam points, and a final revision checklist.", text)
    row = Note(user_id=user.id, title=title, course=course, text=text, summary=summary); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "title": row.title, "course": row.course, "summary": row.summary}

@app.get("/notes")
def notes(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "summary": r.summary, "created_at": r.created_at} for r in rows]

@app.post("/assistant/chat")
def assistant_chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    context_parts = []
    assignments = db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.status != "completed").order_by(Assignment.due_at.asc()).limit(15).all()
    if assignments:
        context_parts.append("Assignments:\n" + "\n".join(f"- {a.title} | {a.course} | due {a.due_at} | {a.progress}% | {a.status}" for a in assignments))
    classes = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id).order_by(TimetableEntry.weekday, TimetableEntry.start_time).all()
    if classes:
        context_parts.append("Weekly timetable:\n" + "\n".join(f"- weekday {c.weekday} {c.start_time}-{c.end_time} | {c.course} | room {c.room or 'not set'}" for c in classes))
    exams = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_at).limit(10).all()
    if exams:
        context_parts.append("Exams:\n" + "\n".join(f"- {e.course} | {e.exam_at} | room {e.room or 'not set'}" for e in exams))
    attendance = attendance_summary(user, db)
    if attendance:
        context_parts.append("Attendance:\n" + "\n".join(f"- {a['course']}: {a['percentage']}% ({a['attended']}/{a['total']})" for a in attendance))
    grade_data = grades(user, db)
    if grade_data["courses"]:
        context_parts.append(f"GPA: {grade_data['gpa']}\nGrades:\n" + "\n".join(f"- {g['course']}: {g['grade_point']} points, {g['credits']} credits" for g in grade_data["courses"]))
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
        "exam": "Act as an exam revision coach. Focus on testable points, recall, and concise marking-friendly answers.",
        "planner": "Create a realistic prioritized academic plan using actual timetable, assignment and exam data. Do not invent times.",
        "focus": "Keep the answer extremely short and give only the next most useful action.",
        "normal": "Answer directly and clearly.",
    }.get(data.mode, "Answer directly and clearly.")
    prompt = f"Mode instruction: {mode_instruction}\nStudent name: {user.name}\nStudent request: {data.message}"
    return {"reply": ai_answer(prompt, "\n\n".join(context_parts))}
