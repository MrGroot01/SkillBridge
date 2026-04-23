from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.models import User, UserRole
from src.schemas.schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    MonitoringTokenRequest
)
from src.auth.jwt import (
    hash_password,
    verify_password,
    create_access_token,
    create_monitoring_token,
    require_role,
)
from src.core.config import settings

# ✅ KEEP PREFIX HERE (IMPORTANT)
router = APIRouter(prefix="/auth", tags=["Auth"])


# -------------------- SIGNUP --------------------
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user and return JWT token"""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate institution (ONLY if provided)
    if payload.institution_id:
        institution = db.query(User).filter(
            User.id == payload.institution_id,
            User.role == UserRole.institution
        ).first()

        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")

    # Create new user
    new_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    access_token = create_access_token(str(new_user.id), new_user.role.value)

    return TokenResponse(access_token=access_token)


# -------------------- LOGIN --------------------
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT"""

    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(str(user.id), user.role.value)

    return TokenResponse(access_token=access_token)


# -------------------- MONITORING TOKEN --------------------
@router.post("/monitoring-token", response_model=TokenResponse)
def get_monitoring_token(
    payload: MonitoringTokenRequest,
    current_user: User = Depends(require_role(UserRole.monitoring_officer)),
):
    """Generate monitoring token (only for monitoring officer)"""

    if payload.key != settings.MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_monitoring_token(str(current_user.id))

    return TokenResponse(access_token=token)