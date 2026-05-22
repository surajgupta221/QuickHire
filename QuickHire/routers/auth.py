from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from schemas.user import UserRegister, UserLogin, Token, UserResponse
import secrets
from datetime import datetime, timedelta
from services.auth import (
    get_user_by_email, create_user,
    verify_password, create_access_token
)

# ─── Router ───────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── Admin: Add Credits (for testing only) ────
@router.post("/admin/add-credits", tags=["Admin"])
def add_credits(
    email: str,
    credits: int,
    admin_key: str,
    db: Session = Depends(get_db)
):
    """Add credits to any account — for testing only"""
    # Simple admin key protection
    if admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.screening_credits += credits
    db.commit()
    db.refresh(user)

    return {
        "message": f"Added {credits} credits",
        "email": email,
        "new_balance": user.screening_credits
    }


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

# Store reset tokens temporarily (use Redis in production)
reset_tokens = {}

@router.post("/forgot-password", tags=["Authentication"])
def forgot_password(email: str, db: Session = Depends(get_db)):
    """Send password reset link"""
    user = get_user_by_email(db, email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If this email exists, a reset link has been sent"}

    # Generate reset token
    token = secrets.token_urlsafe(32)
    reset_tokens[email] = {
        "token": token,
        "expires": datetime.now() + timedelta(hours=1)
    }

    # In production send email — for now return token
    print(f"Reset token for {email}: {token}")

    return {
        "message": "Password reset link sent to your email",
        "debug_token": token  # Remove in production
    }


@router.post("/reset-password", tags=["Authentication"])
def reset_password(
    email: str,
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    if email not in reset_tokens:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    stored = reset_tokens[email]

    if stored["token"] != token:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if datetime.now() > stored["expires"]:
        del reset_tokens[email]
        raise HTTPException(status_code=400, detail="Reset token expired")
    return {
        "message": "Password reset link sent to your email",
        "debug_token": token  # Remove in production
    }


@router.post("/reset-password", tags=["Authentication"])
def reset_password(
    email: str,
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    if email not in reset_tokens:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    stored = reset_tokens[email]

    if stored["token"] != token:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if datetime.now() > stored["expires"]:
        del reset_tokens[email]
        raise HTTPException(status_code=400, detail="Reset token expired")

    # Update user password
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = hash_password(new_password)
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)

    # Remove reset token
    del reset_tokens[email]

    return {"message": "Password reset successfully"}

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