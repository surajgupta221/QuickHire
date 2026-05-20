from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
import enum

# ─── Plan Types ───────────────────────────────
class PlanType(str, enum.Enum):
    free = "free"
    monthly = "monthly"
    annual = "annual"
    pay_per_use = "pay_per_use"

# ─── User Table ───────────────────────────────
# This becomes a table in our database
# Each class variable = one column in the table
class User(Base):
    __tablename__ = "users"

    # Primary Key — unique ID for each user
    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Business Info
    company_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)

    # Account Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    onboarding_complete = Column(Boolean, default=False)

    # Subscription
    plan = Column(String, default="free")
    screening_credits = Column(Integer, default=5)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.email}>"