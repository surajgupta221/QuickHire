from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from schemas.user import UserRegister, UserLogin, Token, UserResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from pydantic import BaseModel
import secrets
from services.sheets_service import add_user_to_sheet
from services.email_service import send_password_reset_email, send_welcome_email
from datetime import datetime, timedelta
from services.auth import (
    get_user_by_email, create_user,hash_password,
    verify_password, create_access_token
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# ─── Router ───────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/google-login", tags=["Authentication"])
def google_login(google_token: str, db: Session = Depends(get_db)):
    """Login or register with Google"""
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo['email']
        full_name = idinfo.get('name', email.split('@')[0])

        user = get_user_by_email(db, email)
        if not user:
            user = create_user(
                db=db,
                full_name=full_name,
                email=email,
                password=secrets.token_urlsafe(32),
                company_name=None,
                phone=None
            )
            send_welcome_email(email, full_name)

        token = create_access_token({"sub": user.email, "user_id": user.id})
        return {"access_token": token, "token_type": "bearer", "user": user}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")


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

    # Send welcome email
    send_welcome_email(user_data.email, user_data.full_name)

    # Add to Google Sheets
    add_user_to_sheet({
        "full_name": user_data.full_name,
        "email": user_data.email,
        "phone": user_data.phone or "",
        "company_name": user_data.company_name or "",
        "plan": "free",
        "screening_credits": 10
    })
    
    # Create JWT token
    token = create_access_token({"sub": user.email, "user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

class LoginRequest(BaseModel):
    email: str
    password: str

# ─── Login ────────────────────────────────────
# ─── Login ────────────────────────────────────
@router.post("/login", tags=["Authentication"])
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""

    print("LOGIN ATTEMPT:", login_data.email, flush=True)

    # Find user
    user = get_user_by_email(db, login_data.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(
        login_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    print("LOGIN SUCCESS", flush=True)

    # Create JWT token
    token = create_access_token({
        "sub": user.email,
        "user_id": user.id
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "company_name": user.company_name,
            "screening_credits": user.screening_credits,
            "plan": user.plan,
            "onboarding_complete": user.onboarding_complete
        }
    }

# Store reset tokens temporarily (use Redis in production)
reset_tokens = {}
@router.post("/forgot-password", tags=["Authentication"])
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        return {"message": "If this email exists, a reset link has been sent"}

    token = secrets.token_urlsafe(32)
    reset_tokens[email] = {
        "token": token,
        "expires": datetime.now() + timedelta(hours=1)
    }

    # Send actual email
    send_password_reset_email(email, token, user.full_name)

    return {"message": "Password reset link sent to your email! Check your inbox."}


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
    from ..services.auth import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user 