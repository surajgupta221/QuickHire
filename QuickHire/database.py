from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

# ─── Database URL ─────────────────────────────
# Using SQLite for development (zero setup!)
# We'll switch to PostgreSQL before deployment
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ─── Create Engine ────────────────────────────
# Engine = connection to database
# Like opening an Excel file
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite only
)

# ─── Session ──────────────────────────────────
# Session = one conversation with database
# Like having one Excel file open at a time
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ─── Base ─────────────────────────────────────
# Base = parent class all our models inherit from
# Like a template for all our database tables
Base = declarative_base()

# ─── Dependency ───────────────────────────────
# This function gives us a database session
# We'll use this in every API endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()