from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import user, screening as screening_model
from routers import auth, screening
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ─── Create tables ────────────────────────────
Base.metadata.create_all(bind=engine)


# ─── Create App ───────────────────────────────
app = FastAPI(
    title="QuickHire",
    description="AI-Powered Recruitment Assistant for Smart Recruiters",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Add after creating app
app.mount("/static", StaticFiles(directory="."), name="static")

# ─── Include Routers ──────────────────────────
app.include_router(auth.router)
app.include_router(screening.router)

# ─── CORS Middleware ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Root Endpoint ────────────────────────────
@app.get("/", tags=["Health"])
def home():
    return {
        "app": "QuickHire",
        "version": "1.0.0",
        "status": "running",
        "message": "AI Recruitment Assistant is live!"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

@app.get("/test")
def test_page():
    return FileResponse("test_upload.html")

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
            "free": "3 screenings",
            "pay_per_use": "₹49/screening",
            "monthly": "₹1,599/month",
            "annual": "₹14,999/year"
        }
    }