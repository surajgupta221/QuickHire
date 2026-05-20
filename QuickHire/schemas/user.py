from pydantic import BaseModel, EmailStr
from typing import Optional

# ─── What user sends to REGISTER ──────────────
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr        # validates email format
    password: str
    company_name: Optional[str] = None
    phone: Optional[str] = None

# ─── What user sends to LOGIN ─────────────────
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ─── What we send BACK to user ────────────────
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    company_name: Optional[str]
    screening_credits: int
    plan: str
    onboarding_complete: bool

    class Config:
        from_attributes = True

# ─── Token Response ───────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse