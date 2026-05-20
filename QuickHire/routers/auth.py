from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserRegister, UserLogin, Token, UserResponse
from services.auth import (
    get_user_by_email, create_user,
    verify_password, create_access_token
)

# ─── Router ───────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── Register ─────────────────────────────────
@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new recruiter account"""

    # Check if email already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user
    user = create_user(
        db=db,
        full_name=user_data.full_name,
        email=user_data.email,
        password=user_data.password,
        company_name=user_data.company_name,
        phone=user_data.phone
    )

    # Create JWT token
    token = create_access_token({"sub": user.email, "user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

# ─── Login ────────────────────────────────────
@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""

    # Find user
    user = get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Check password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create token
    token = create_access_token({"sub": user.email, "user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

# ─── Get Current User Info ────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(token: str, db: Session = Depends(get_db)):
    """Get current logged in user details"""
    from services.auth import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user