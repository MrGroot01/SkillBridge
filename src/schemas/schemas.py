from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import date, time, datetime

from src.models.models import UserRole, AttendanceStatus


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    institution_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    key: str


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    institution_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Batch Schemas ────────────────────────────────────────────────────────────

class BatchCreate(BaseModel):
    name: str
    institution_id: str


class BatchOut(BaseModel):
    id: str
    name: str
    institution_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteCreate(BaseModel):
    batch_id: str  # used internally; from path param


class InviteOut(BaseModel):
    id: str
    batch_id: str
    token: str
    expires_at: datetime
    used: bool

    model_config = {"from_attributes": True}


class JoinBatchRequest(BaseModel):
    token: str


# ─── Session Schemas ──────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: str


class SessionOut(BaseModel):
    id: str
    batch_id: str
    trainer_id: str
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Attendance Schemas ───────────────────────────────────────────────────────

class AttendanceMark(BaseModel):
    session_id: str
    status: AttendanceStatus = AttendanceStatus.present


class AttendanceOut(BaseModel):
    id: str
    session_id: str
    student_id: str
    status: AttendanceStatus
    marked_at: datetime

    model_config = {"from_attributes": True}


class AttendanceWithStudent(BaseModel):
    student_id: str
    student_name: str
    student_email: str
    status: AttendanceStatus
    marked_at: datetime

    model_config = {"from_attributes": True}


# ─── Summary Schemas ──────────────────────────────────────────────────────────

class BatchSummary(BaseModel):
    batch_id: str
    batch_name: str
    total_sessions: int
    total_students: int
    total_attendance_marks: int
    present_count: int
    absent_count: int
    late_count: int
    attendance_rate: float


class InstitutionSummary(BaseModel):
    institution_id: str
    institution_name: str
    total_batches: int
    batch_summaries: List[BatchSummary]


class ProgrammeSummary(BaseModel):
    total_institutions: int
    total_batches: int
    total_sessions: int
    total_students: int
    overall_attendance_rate: float
    institution_summaries: List[InstitutionSummary]


# ─── Error Schemas ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
