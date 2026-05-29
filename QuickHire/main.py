import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Python version:", sys.version, flush=True)
print("Starting QuickHire...", flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings
from models import user, screening as screening_model, payment as payment_model
from routers import auth, screening, payment

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!", flush=True)
except Exception as e:
    print(f"❌ Table creation error: {e}", flush=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Recruitment Assistant for Smart Recruiters",
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(screening.router)
app.include_router(payment.router)

@app.get("/", tags=["Health"])
def home():
    return {"app": "QuickHire", "version": "1.0.0", "status": "running"}

@app.get("/health", tags=["Health"])
@app.head("/health")
def health():
    return {"status": "healthy"}

@app.get("/init-db", tags=["Health"])
def init_db():
    try:
        # Create new tables
        Base.metadata.create_all(bind=engine)

        # Add missing columns if they don't exist
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                conn.execute(text(
                    "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS must_have_skills VARCHAR"
                ))
                conn.execute(text(
                    "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS good_to_have_skills VARCHAR"
                ))
                conn.commit()
                print("✅ Columns added!", flush=True)
            except Exception as col_err:
                print(f"Column note: {col_err}", flush=True)

        return {"message": "Database updated successfully!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/info", tags=["Health"])
def info():
    return {
        "plans": {
            "free": "5 screenings",
            "pay_per_use": "₹49/screening",
            "monthly": "₹1,999/month",
            "annual": "₹19,999/year"
        }
    }