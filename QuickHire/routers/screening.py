from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.screening import Screening
from models.user import User
from services.file_parser import extract_text_from_file
from services.ai_scorer import score_multiple_resumes
from services.auth import verify_token
from services.excel_export import export_results_to_excel
import io

router = APIRouter(prefix="/screening", tags=["Screening"])

# ─── Helper ───────────────────────────────────
def get_current_user(token: str, db: Session):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(
        User.email == payload.get("sub")
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ─── Upload JD ────────────────────────────────
@router.post("/upload-jd")
async def upload_jd(
    job_title: str = Form(...),
    location: str = Form(""),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload Job Description as file or pasted text"""
    user = get_current_user(token, db)

    if user.screening_credits <= 0:
        raise HTTPException(
            status_code=403,
            detail="No credits left. Please upgrade your plan."
        )

    if jd_file and jd_file.filename:
        extracted_jd = await extract_text_from_file(jd_file)
    elif jd_text:
        extracted_jd = jd_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide JD as file or text"
        )

    screening = Screening(
        user_id=user.id,
        job_title=job_title,
        jd_text=extracted_jd,
        location=location,
        status="pending"
    )
    db.add(screening)
    db.commit()
    db.refresh(screening)

    return {
        "message": "JD uploaded successfully",
        "screening_id": screening.id,
        "job_title": job_title,
        "jd_preview": extracted_jd[:200] + "..." if len(extracted_jd) > 200 else extracted_jd
    }

# ─── Upload Resumes ───────────────────────────
@router.post("/upload-resumes/{screening_id}")
async def upload_resumes(
    screening_id: int,
    token: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload 1 to 20 resumes at once.
    Supported formats: PDF, Word (.docx), Text (.txt)
    Select multiple files by holding Ctrl key.
    """
    user = get_current_user(token, db)

    screening = db.query(Screening).filter(
        Screening.id == screening_id,
        Screening.user_id == user.id
    ).first()

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    uploaded_files = [f for f in resumes if f and f.filename]

    if not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one resume"
        )

    if len(uploaded_files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 resumes allowed per screening"
        )

    # Extract text from each resume
    resume_data = []
    for resume_file in uploaded_files:
        try:
            text = await extract_text_from_file(resume_file)
            name = resume_file.filename
            for ext in ['.pdf', '.docx', '.doc', '.txt', '.PDF', '.DOCX']:
                name = name.replace(ext, '')
            resume_data.append({
                "name": name.strip(),
                "text": text,
                "filename": resume_file.filename
            })
        except Exception as e:
            resume_data.append({
                "name": resume_file.filename,
                "text": "Could not read file",
                "filename": resume_file.filename,
                "error": str(e)
            })

    screening.status = "processing"
    db.commit()

    results = score_multiple_resumes(screening.jd_text, resume_data)

    screening.results = results
    screening.total_candidates = len(results)
    screening.status = "completed"
    user.screening_credits -= 1
    db.commit()

    return {
        "message": "Screening completed!",
        "screening_id": screening_id,
        "job_title": screening.job_title,
        "total_candidates": len(results),
        "credits_remaining": user.screening_credits,
        "results": results
    }

# ─── Get Results ──────────────────────────────
@router.get("/results/{screening_id}")
def get_results(
    screening_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get results of a completed screening"""
    user = get_current_user(token, db)
    screening = db.query(Screening).filter(
        Screening.id == screening_id,
        Screening.user_id == user.id
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    return {
        "screening_id": screening_id,
        "job_title": screening.job_title,
        "location": screening.location,
        "status": screening.status,
        "total_candidates": screening.total_candidates,
        "results": screening.results,
        "created_at": screening.created_at
    }

# ─── History ──────────────────────────────────
@router.get("/history")
def get_history(token: str, db: Session = Depends(get_db)):
    """Get all past screenings"""
    user = get_current_user(token, db)
    screenings = db.query(Screening).filter(
        Screening.user_id == user.id
    ).order_by(Screening.created_at.desc()).all()
    return {
        "total": len(screenings),
        "screenings": [
            {
                "id": s.id,
                "job_title": s.job_title,
                "location": s.location,
                "total_candidates": s.total_candidates,
                "status": s.status,
                "created_at": s.created_at
            }
            for s in screenings
        ]
    }

# ─── Export Excel ─────────────────────────────
@router.get("/export/{screening_id}")
def export_to_excel(
    screening_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Download results as Excel file"""
    user = get_current_user(token, db)
    screening = db.query(Screening).filter(
        Screening.id == screening_id,
        Screening.user_id == user.id
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    if not screening.results:
        raise HTTPException(status_code=400, detail="No results yet")

    excel_bytes = export_results_to_excel(
        job_title=screening.job_title,
        results=screening.results
    )
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=QuickHire_{screening.job_title}.xlsx"
        }
    )