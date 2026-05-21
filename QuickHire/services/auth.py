from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models.user import User
import os
from dotenv import load_dotenv
from config import settings

# ─── Config ───────────────────────────────────
load_dotenv()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ─── Password Hashing ─────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Convert plain password to hashed version"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches hashed one"""
    return pwd_context.verify(plain_password, hashed_password)

# ─── JWT Token ────────────────────────────────
def create_access_token(data: dict) -> str:
    """Create a JWT token that expires in 24 hours"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ─── Database Helpers ─────────────────────────
def get_user_by_email(db: Session, email: str):
    """Find user by email in database"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, full_name: str, email: str,
                password: str, company_name: str = None,
                phone: str = None):
    """Create new user in database"""
    hashed = hash_password(password)
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hashed,
        company_name=company_name,
        phone=phone,
        screening_credits=3,  # Free tier gets 3 credits
        plan="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user