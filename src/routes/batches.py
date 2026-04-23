import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.models import (
    User, Batch, BatchTrainer, BatchStudent, BatchInvite, UserRole
)
from src.schemas.schemas import BatchCreate, BatchOut, InviteOut, JoinBatchRequest
from src.auth.jwt import require_role, get_current_user

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("", response_model=BatchOut, status_code=201)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.trainer, UserRole.institution)),
):
    """Trainer or Institution creates a batch."""
    inst = db.query(User).filter(
        User.id == payload.institution_id,
        User.role == UserRole.institution
    ).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = Batch(name=payload.name, institution_id=payload.institution_id)
    db.add(batch)
    db.flush()

    # Auto-assign trainer if creator is a trainer
    if current_user.role == UserRole.trainer:
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=current_user.id))

    db.commit()
    db.refresh(batch)
    return batch


@router.post("/{batch_id}/invite", response_model=InviteOut, status_code=201)
def create_invite(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.trainer)),
):
    """Trainer generates an invite token for a batch they manage."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Ensure trainer is assigned to this batch
    assignment = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == batch_id,
        BatchTrainer.trainer_id == current_user.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not a trainer for this batch")

    invite = BatchInvite(
        batch_id=batch_id,
        token=str(uuid.uuid4()),
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/join", status_code=200)
def join_batch(
    payload: JoinBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    """Student uses an invite token to join a batch."""
    invite = db.query(BatchInvite).filter(BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    if invite.used:
        raise HTTPException(status_code=400, detail="Invite token already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite token expired")

    # Check student not already in batch
    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this batch")

    db.add(BatchStudent(batch_id=invite.batch_id, student_id=current_user.id))
    invite.used = True
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": str(invite.batch_id)}
