import sys
import os
import models
# Force Python to find the local 'services' and 'routers' folders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print("Python version:", sys.version)
print("Starting QuickHire...")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from database import engine, Base
from config import settings
from models import user, screening as screening_model, payment as payment_model
from routers import auth, screening, payment


# Create tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully!", flush=True)
except Exception as e:
    print(f"❌ Table creation error: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Create App
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Recruitment Assistant for Smart Recruiters",
    version=settings.APP_VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://quick-hire-lime.vercel.app",  # Production Frontend
        "https://quick-hire-yzwt.vercel.app",  # 👈 ADD THIS: Staging Frontend
        "https://quickhire.vercel.app",
        
    ]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(screening.router)
app.include_router(payment.router)

# Test Page
@app.get("/test", response_class=HTMLResponse)
def test_page():
    with open("quicktest.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/init-db", tags=["Health"])
def init_db():
    """Force database table creation"""
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Database tables created successfully!"}
    except Exception as e:
        return {"error": str(e)}
    
# Health endpoints
@app.get("/", tags=["Health"])
def home():
    return {
        "app": "QuickHire",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

@app.get("/info", tags=["Health"])
def info():
    return {
        "features": [
            "Resume Upload Screening",
            "LinkedIn Profile Search",
            "AI Scoring 0-100",
            "Excel Export",
            "Email Automation"
        ],
        "plans": {
            "free": "5 screenings",
            "pay_per_use": "₹49/screening",
            "monthly": "₹1,999/month",
            "annual": "₹19,999/year"
        }
    }