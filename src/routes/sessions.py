import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from src.core.database import get_db
from src.models.models import User, Batch, BatchTrainer, Session, UserRole
from src.schemas.schemas import SessionCreate, SessionOut
from src.auth.jwt import require_role

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.trainer)),
):
    """Trainer creates a session for a batch they manage."""
    batch = db.query(Batch).filter(Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Confirm trainer is assigned to this batch
    assigned = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == payload.batch_id,
        BatchTrainer.trainer_id == current_user.id
    ).first()
    if not assigned:
        raise HTTPException(status_code=403, detail="You are not a trainer for this batch")

    session = Session(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
