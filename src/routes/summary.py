import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from src.core.database import get_db
from src.models.models import (
    User, Batch, BatchStudent, Session, Attendance, UserRole, AttendanceStatus
)
from src.schemas.schemas import BatchSummary, InstitutionSummary, ProgrammeSummary
from src.auth.jwt import require_role
from typing import List

router = APIRouter(tags=["Summary"])


def _batch_summary(batch: Batch, db: DBSession) -> BatchSummary:
    total_sessions = db.query(Session).filter(Session.batch_id == batch.id).count()
    total_students = db.query(BatchStudent).filter(BatchStudent.batch_id == batch.id).count()

    att_q = db.query(Attendance).join(Session, Attendance.session_id == Session.id).filter(
        Session.batch_id == batch.id
    )
    total_marks = att_q.count()
    present = att_q.filter(Attendance.status == AttendanceStatus.present).count()
    absent = att_q.filter(Attendance.status == AttendanceStatus.absent).count()
    late = att_q.filter(Attendance.status == AttendanceStatus.late).count()
    rate = round((present / total_marks * 100) if total_marks > 0 else 0.0, 2)

    return BatchSummary(
        batch_id=batch.id,
        batch_name=batch.name,
        total_sessions=total_sessions,
        total_students=total_students,
        total_attendance_marks=total_marks,
        present_count=present,
        absent_count=absent,
        late_count=late,
        attendance_rate=rate,
    )


@router.get("/batches/{batch_id}/summary", response_model=BatchSummary)
def batch_summary(
    batch_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.institution, UserRole.programme_manager)),
):
    """Institution views attendance summary for a specific batch."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batch_summary(batch, db)


@router.get("/institutions/{institution_id}/summary", response_model=InstitutionSummary)
def institution_summary(
    institution_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.programme_manager)),
):
    """Programme Manager views all batches under an institution."""
    institution = db.query(User).filter(
        User.id == institution_id,
        User.role == UserRole.institution
    ).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batches = db.query(Batch).filter(Batch.institution_id == institution_id).all()
    return InstitutionSummary(
        institution_id=institution.id,
        institution_name=institution.name,
        total_batches=len(batches),
        batch_summaries=[_batch_summary(b, db) for b in batches],
    )


@router.get("/programme/summary", response_model=ProgrammeSummary)
def programme_summary(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.programme_manager)),
):
    """Programme Manager views programme-wide summary."""
    institutions = db.query(User).filter(User.role == UserRole.institution).all()
    total_batches = db.query(Batch).count()
    total_sessions = db.query(Session).count()
    total_students = db.query(User).filter(User.role == UserRole.student).count()
    total_marks = db.query(Attendance).count()
    present = db.query(Attendance).filter(Attendance.status == AttendanceStatus.present).count()
    overall_rate = round((present / total_marks * 100) if total_marks > 0 else 0.0, 2)

    institution_summaries = []
    for inst in institutions:
        batches = db.query(Batch).filter(Batch.institution_id == inst.id).all()
        institution_summaries.append(InstitutionSummary(
            institution_id=inst.id,
            institution_name=inst.name,
            total_batches=len(batches),
            batch_summaries=[_batch_summary(b, db) for b in batches],
        ))

    return ProgrammeSummary(
        total_institutions=len(institutions),
        total_batches=total_batches,
        total_sessions=total_sessions,
        total_students=total_students,
        overall_attendance_rate=overall_rate,
        institution_summaries=institution_summaries,
    )
