from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import fitz
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

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
    academic_year: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    student_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    campus: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
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


class FeeItem(Base):
    __tablename__ = "campus_fees"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    amount_due: Mapped[float] = mapped_column(Float)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    semester: Mapped[str] = mapped_column(String(80), default="Current")


class AIMemory(Base):
    __tablename__ = "campus_ai_memory"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    key: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIMessage(Base):
    __tablename__ = "campus_ai_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("campus_users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
app = FastAPI(title="Campus Hub API", version="1.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def gemini_request(parts: list[dict], temperature: float = 0.3) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    request_body = {"contents": [{"parts": parts}], "generationConfig": {"temperature": temperature}}
    request = urllib.request.Request(
        f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"[smith] Gemini API error {exc.code}: {body[:800]}")
        raise RuntimeError("Gemini is temporarily unavailable") from exc
    except Exception as exc:
        print(f"[smith] Gemini request failed: {exc}")
        raise RuntimeError("Gemini is temporarily unavailable") from exc
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no response")
    reply = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])).strip()
    if not reply:
        raise RuntimeError("Gemini returned an empty response")
    return reply


def ai_answer(prompt: str, context: str = "") -> str:
    if not GEMINI_API_KEY:
        return fallback_summary(context or prompt)
    combined = (
        "You are Smith, Campus Hub's academic assistant for an ISBAT University student. "
        "Be concise, accurate, practical and student-friendly. Use supplied academic context. "
        "Never invent class times, assignment dates, exam dates, grades, attendance, fee balances or note content. "
        "If data is missing, say so clearly.\n\n"
        f"Academic context:\n{context[:100000]}\n\nStudent request:\n{prompt}"
    )
    try:
        return gemini_request([{"text": combined}])
    except RuntimeError:
        return fallback_summary(context or prompt)


def scanned_pdf_text(doc: fitz.Document) -> str:
    if not GEMINI_API_KEY:
        return ""
    parts: list[dict] = [{"text": "Read these scanned lecture-note pages. Extract the visible academic text faithfully in reading order. Do not summarize yet."}]
    for page in list(doc)[:4]:
        pix = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        parts.append({"inlineData": {"mimeType": "image/png", "data": base64.b64encode(pix.tobytes("png")).decode("ascii")}})
    try:
        return clean_text(gemini_request(parts, 0.1))
    except RuntimeError:
        return ""


def profile_dict(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "university": user.university or "ISBAT University",
        "programme": user.programme,
        "semester": user.semester,
        "academic_year": user.academic_year,
        "student_number": user.student_number,
        "campus": user.campus,
    }


def owned(db: Session, model, row_id, user_id: int):
    row = db.get(model, row_id)
    if not row or row.user_id != user_id:
        raise HTTPException(404, "Record not found")
    return row


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
    academic_year: Optional[str] = None
    student_number: Optional[str] = None
    campus: Optional[str] = None


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


class FeeIn(BaseModel):
    title: str
    amount_due: float = Field(ge=0)
    amount_paid: float = Field(default=0, ge=0)
    due_at: Optional[datetime] = None
    semester: str = "Current"


class MemoryIn(BaseModel):
    key: str
    value: str


class ChatIn(BaseModel):
    message: str
    mode: str = "normal"
    documentId: Optional[str] = None


@app.get("/")
def root():
    return {"service": "Campus Hub API", "status": "online", "docs": "/docs"}


@app.get("/health")
def health():
    return {"ok": True, "service": "campus-hub-api", "version": "1.3.0", "ai_provider": "gemini" if GEMINI_API_KEY else "fallback", "database": "postgres" if DATABASE_URL.startswith("postgres") else "sqlite"}


@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(db_session)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name.strip() or "Student", email=data.email.lower(), password_hash=pwd_context.hash(data.password), university="ISBAT University")
    db.add(user); db.commit(); db.refresh(user)
    return {"token": token_for(user.id), "user": profile_dict(user)}


@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not user.university:
        user.university = "ISBAT University"; db.commit()
    return {"token": token_for(user.id), "user": profile_dict(user)}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return profile_dict(user)


@app.patch("/me")
def update_me(data: ProfileIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    values = data.model_dump(exclude_unset=True)
    values["university"] = "ISBAT University"
    for k, v in values.items():
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


@app.patch("/assignments/{row_id}")
def update_assignment(row_id: int, data: AssignmentIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, Assignment, row_id, user.id)
    for k, v in data.model_dump().items(): setattr(row, k, v)
    db.commit(); db.refresh(row)
    return {"id": row.id, "title": row.title, "course": row.course, "due_at": row.due_at, "progress": row.progress, "status": row.status}


@app.delete("/assignments/{row_id}")
def delete_assignment(row_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, Assignment, row_id, user.id); db.delete(row); db.commit(); return {"ok": True}


@app.get("/timetable")
def get_timetable(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id).order_by(TimetableEntry.weekday, TimetableEntry.start_time).all()
    return [{"id": r.id, "course": r.course, "lecturer": r.lecturer, "room": r.room, "weekday": r.weekday, "start_time": r.start_time, "end_time": r.end_time} for r in rows]


def validate_time(value: str):
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise HTTPException(422, "Times must use HH:MM format")


@app.post("/timetable")
def add_timetable(data: TimetableIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    validate_time(data.start_time); validate_time(data.end_time)
    row = TimetableEntry(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}


@app.patch("/timetable/{row_id}")
def update_timetable(row_id: int, data: TimetableIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    validate_time(data.start_time); validate_time(data.end_time)
    row = owned(db, TimetableEntry, row_id, user.id)
    for k, v in data.model_dump().items(): setattr(row, k, v)
    db.commit(); return {"ok": True}


@app.delete("/timetable/{row_id}")
def delete_timetable(row_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, TimetableEntry, row_id, user.id); db.delete(row); db.commit(); return {"ok": True}


@app.get("/exams")
def get_exams(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_at).all()
    return [{"id": r.id, "course": r.course, "exam_at": r.exam_at, "room": r.room} for r in rows]


@app.post("/exams")
def add_exam(data: ExamIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Exam(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, **data.model_dump()}


@app.patch("/exams/{row_id}")
def update_exam(row_id: int, data: ExamIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, Exam, row_id, user.id)
    for k, v in data.model_dump().items(): setattr(row, k, v)
    db.commit(); return {"ok": True}


@app.delete("/exams/{row_id}")
def delete_exam(row_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, Exam, row_id, user.id); db.delete(row); db.commit(); return {"ok": True}


@app.get("/attendance")
def attendance_summary(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Attendance).filter(Attendance.user_id == user.id).all(); grouped = {}
    for r in rows:
        item = grouped.setdefault(r.course, {"course": r.course, "attended": 0, "total": 0})
        item["total"] += 1; item["attended"] += 1 if r.attended else 0
    return [{**v, "percentage": round((v["attended"] / v["total"]) * 100, 1) if v["total"] else 0} for v in grouped.values()]


@app.post("/attendance")
def add_attendance(data: AttendanceIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Attendance(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row); return {"id": row.id, **data.model_dump()}


@app.get("/grades")
def grades(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Grade).filter(Grade.user_id == user.id).all(); credits = sum(r.credits for r in rows)
    gpa = round(sum(r.credits * r.grade_point for r in rows) / credits, 2) if credits else None
    return {"gpa": gpa, "courses": [{"id": r.id, "course": r.course, "credits": r.credits, "grade_point": r.grade_point, "semester": r.semester} for r in rows]}


@app.post("/grades")
def add_grade(data: GradeIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = Grade(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row); return {"id": row.id, **data.model_dump()}


@app.delete("/grades/{row_id}")
def delete_grade(row_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, Grade, row_id, user.id); db.delete(row); db.commit(); return {"ok": True}


@app.get("/fees")
def fees(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(FeeItem).filter(FeeItem.user_id == user.id).order_by(FeeItem.due_at.asc()).all()
    total_due = sum(r.amount_due for r in rows); total_paid = sum(r.amount_paid for r in rows)
    return {"total_due": total_due, "total_paid": total_paid, "balance": max(0, total_due-total_paid), "items": [{"id": r.id, "title": r.title, "amount_due": r.amount_due, "amount_paid": r.amount_paid, "balance": max(0, r.amount_due-r.amount_paid), "due_at": r.due_at, "semester": r.semester} for r in rows]}


@app.post("/fees")
def add_fee(data: FeeIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = FeeItem(user_id=user.id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row); return {"id": row.id, **data.model_dump()}


@app.patch("/fees/{row_id}")
def update_fee(row_id: int, data: FeeIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, FeeItem, row_id, user.id)
    for k, v in data.model_dump().items(): setattr(row, k, v)
    db.commit(); return {"ok": True}


@app.delete("/fees/{row_id}")
def delete_fee(row_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = owned(db, FeeItem, row_id, user.id); db.delete(row); db.commit(); return {"ok": True}


@app.get("/memory")
def memories(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(AIMemory).filter(AIMemory.user_id == user.id).order_by(AIMemory.created_at.desc()).all()
    return [{"id": r.id, "key": r.key, "value": r.value} for r in rows]


@app.post("/memory")
def remember(data: MemoryIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = db.query(AIMemory).filter(AIMemory.user_id == user.id, AIMemory.key == data.key).first()
    if row: row.value = data.value
    else: row = AIMemory(user_id=user.id, **data.model_dump()); db.add(row)
    db.commit(); db.refresh(row); return {"id": row.id, "key": row.key, "value": row.value}


@app.get("/assistant/history")
def assistant_history(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(AIMessage).filter(AIMessage.user_id == user.id).order_by(AIMessage.id.desc()).limit(40).all()[::-1]
    return [{"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at} for r in rows]


@app.delete("/assistant/history")
def clear_assistant_history(user: User = Depends(current_user), db: Session = Depends(db_session)):
    db.query(AIMessage).filter(AIMessage.user_id == user.id).delete(); db.commit(); return {"ok": True}


@app.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(db_session)):
    now = datetime.now(); weekday = now.weekday()
    today = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id, TimetableEntry.weekday == weekday).order_by(TimetableEntry.start_time).all()
    assignments = db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.status != "completed").order_by(Assignment.due_at.asc()).limit(5).all()
    exams = db.query(Exam).filter(Exam.user_id == user.id, Exam.exam_at >= now).order_by(Exam.exam_at).limit(3).all()
    grade_data = grades(user, db); fee_data = fees(user, db)
    return {"profile": profile_dict(user), "classes": [{"id": r.id, "course": r.course, "room": r.room, "start_time": r.start_time, "end_time": r.end_time} for r in today], "assignments": [{"id": r.id, "title": r.title, "course": r.course, "due_at": r.due_at, "progress": r.progress, "status": r.status} for r in assignments], "exams": [{"id": r.id, "course": r.course, "exam_at": r.exam_at, "room": r.room} for r in exams], "gpa": grade_data["gpa"], "fee_balance": fee_data["balance"]}


@app.post("/notes/upload")
async def upload_note(file: UploadFile = File(...), course: str = "General", user: User = Depends(current_user), db: Session = Depends(db_session)):
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF")
    raw = await file.read()
    if len(raw) > 18 * 1024 * 1024:
        raise HTTPException(413, "PDF is too large. Maximum size is 18 MB")
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
        text = clean_text("\n".join(page.get_text("text") for page in doc))
        if len(text) < 80:
            text = scanned_pdf_text(doc)
    except Exception:
        raise HTTPException(400, "This PDF could not be read")
    if len(text) < 80:
        raise HTTPException(422, "This scanned PDF could not be read clearly. Try a clearer scan")
    title = os.path.splitext(file.filename or "Lecture notes")[0]
    summary = ai_answer("Summarize these lecture notes into exam-ready points. Include definitions, key ideas, important examples, likely exam points, and a final revision checklist.", text)
    row = Note(user_id=user.id, title=title, course=course, text=text, summary=summary); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "title": row.title, "course": row.course, "summary": row.summary}


@app.get("/notes")
def notes(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()
    return [{"id": r.id, "title": r.title, "course": r.course, "summary": r.summary, "created_at": r.created_at} for r in rows]


@app.delete("/notes/{note_id}")
def delete_note(note_id: str, user: User = Depends(current_user), db: Session = Depends(db_session)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id).first()
    if not note: raise HTTPException(404, "Note not found")
    db.delete(note); db.commit(); return {"ok": True}


@app.post("/assistant/chat")
def assistant_chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    context_parts = [f"University: ISBAT University\nProgramme: {user.programme or 'not set'}\nSemester: {user.semester or 'not set'}"]
    assignments = db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.status != "completed").order_by(Assignment.due_at.asc()).limit(15).all()
    if assignments: context_parts.append("Assignments:\n" + "\n".join(f"- {a.title} | {a.course} | due {a.due_at} | {a.progress}% | {a.status}" for a in assignments))
    classes = db.query(TimetableEntry).filter(TimetableEntry.user_id == user.id).order_by(TimetableEntry.weekday, TimetableEntry.start_time).all()
    if classes: context_parts.append("Weekly timetable:\n" + "\n".join(f"- weekday {c.weekday} {c.start_time}-{c.end_time} | {c.course} | room {c.room or 'not set'}" for c in classes))
    exams = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_at).limit(10).all()
    if exams: context_parts.append("Exams:\n" + "\n".join(f"- {e.course} | {e.exam_at} | room {e.room or 'not set'}" for e in exams))
    attendance = attendance_summary(user, db)
    if attendance: context_parts.append("Attendance:\n" + "\n".join(f"- {a['course']}: {a['percentage']}%" for a in attendance))
    grade_data = grades(user, db)
    if grade_data["courses"]: context_parts.append(f"GPA: {grade_data['gpa']}\nGrades:\n" + "\n".join(f"- {g['course']}: {g['grade_point']} points" for g in grade_data["courses"]))
    fee_data = fees(user, db)
    if fee_data["items"]: context_parts.append(f"Fees balance: {fee_data['balance']}\n" + "\n".join(f"- {f['title']}: balance {f['balance']} due {f['due_at']}" for f in fee_data["items"]))
    memory_rows = db.query(AIMemory).filter(AIMemory.user_id == user.id).order_by(AIMemory.created_at.desc()).limit(12).all()
    if memory_rows: context_parts.append("Student preferences/memory:\n" + "\n".join(f"- {m.key}: {m.value}" for m in memory_rows))
    history = db.query(AIMessage).filter(AIMessage.user_id == user.id).order_by(AIMessage.id.desc()).limit(8).all()[::-1]
    if history: context_parts.append("Recent Smith conversation:\n" + "\n".join(f"{m.role}: {m.content[:1200]}" for m in history))
    if data.documentId:
        note = db.query(Note).filter(Note.id == data.documentId, Note.user_id == user.id).first()
        if note: context_parts.append(f"Selected note: {note.title}\n{note.text}")
    else:
        for n in db.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).limit(3).all():
            context_parts.append(f"Recent note: {n.title}\n{n.summary or n.text[:5000]}")
    mode_instruction = {"tutor": "Teach step by step, then ask one short check question.", "exam": "Act as an exam revision coach. Focus on testable points and marking-friendly answers.", "planner": "Create a realistic prioritized plan using actual timetable, assignment and exam data. Do not invent times.", "focus": "Keep the answer extremely short and give only the next useful action.", "normal": "Answer directly and clearly."}.get(data.mode, "Answer directly and clearly.")
    prompt = f"Mode instruction: {mode_instruction}\nStudent name: {user.name}\nStudent request: {data.message}"
    reply = ai_answer(prompt, "\n\n".join(context_parts))
    db.add(AIMessage(user_id=user.id, role="user", content=data.message)); db.add(AIMessage(user_id=user.id, role="assistant", content=reply)); db.commit()
    return {"reply": reply}
