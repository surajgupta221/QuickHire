import sys
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings
from models import user, screening as screening_model, payment as payment_model
from routers import auth, screening, payment

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Python version:", sys.version, flush=True)
print("Starting QuickHire...", flush=True)

# Auto-create database tables on application startup
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

# CORS configuration allowing flexible access for testing environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(screening.router)
app.include_router(payment.router)

# Health & Status Validation Routes
@app.get("/", tags=["Health"])
def home():
    return {"app": "QuickHire", "version": "1.0.0", "status": "running"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """Cleanly catches both GET and HEAD network methods for Render pings"""
    return Response(content="OK", status_code=200, media_type="text/plain")

@app.get("/init-db", tags=["Health"])
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Database tables created successfully!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/info", tags=["Health"])
def info():
    return {
        "plans": {
            "free": "10 screenings",
            "pay_per_use": "₹49/screening",
            "monthly": "₹1,999/month",
            "annual": "₹19,999/year"
        }
    }
