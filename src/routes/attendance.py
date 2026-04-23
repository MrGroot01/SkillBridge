import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from src.core.database import get_db
from src.models.models import (
    User, Session, Attendance, BatchStudent, UserRole, AttendanceStatus
)
from src.schemas.schemas import AttendanceMark, AttendanceOut, AttendanceWithStudent
from src.auth.jwt import require_role, get_monitoring_user
from typing import List

router = APIRouter(tags=["Attendance"])


@router.post("/attendance/mark", response_model=AttendanceOut, status_code=201)
def mark_attendance(
    payload: AttendanceMark,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    """Student marks their own attendance for an active session."""
    session = db.query(Session).filter(Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check student is enrolled in the batch for this session
    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == current_user.id
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in the batch for this session")

    # Prevent duplicate marking
    existing = db.query(Attendance).filter(
        Attendance.session_id == payload.session_id,
        Attendance.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this session")

    record = Attendance(
        session_id=payload.session_id,
        student_id=current_user.id,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/sessions/{session_id}/attendance", response_model=List[AttendanceWithStudent])
def get_session_attendance(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.trainer)),
):
    """Trainer views full attendance list for a session."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    result = []
    for r in records:
        result.append(AttendanceWithStudent(
            student_id=r.student_id,
            student_name=r.student.name,
            student_email=r.student.email,
            status=r.status,
            marked_at=r.marked_at,
        ))
    return result


# ─── Monitoring Endpoint ──────────────────────────────────────────────────────

@router.get("/monitoring/attendance")
def monitoring_get_attendance(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_monitoring_user),
):
    """Read-only monitoring view. Requires monitoring-scoped token."""
    records = db.query(Attendance).limit(500).all()
    return [
        {
            "attendance_id": str(r.id),
            "session_id": str(r.session_id),
            "student_id": str(r.student_id),
            "student_name": r.student.name,
            "status": r.status.value,
            "marked_at": r.marked_at.isoformat(),
        }
        for r in records
    ]


@router.post("/monitoring/attendance")
@router.put("/monitoring/attendance")
@router.patch("/monitoring/attendance")
@router.delete("/monitoring/attendance")
def monitoring_reject_non_get(request: Request):
    """Monitoring endpoint rejects any non-GET method with 405."""
    raise HTTPException(status_code=405, detail="Method Not Allowed. Only GET is permitted on monitoring endpoints.")
