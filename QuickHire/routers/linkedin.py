import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from services.auth import verify_token
from services.candidate_sourcer import (
    multi_source_search,
    build_xray_query,
    find_email_hunter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/linkedin", tags=["Candidate Search"])


def get_current_user(token: str, db: Session) -> User:
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == payload.get("sub")).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/search")
def search_candidates(
    job_title: str,
    token: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    jd_text: str = "",
    num_results: int = 10,
    sources: str = "linkedin,github,web",
    source: str = "",
    db: Session = Depends(get_db),
):
    user = get_current_user(token, db)

    if user.screening_credits <= 0:
        raise HTTPException(
            status_code=403,
            detail="No credits left. Please upgrade your plan.",
        )

    if source and not sources:
        sources = source

    if source:
        sources = source

    source_list = [s.strip() for s in sources.split(",") if s.strip()]

    logger.info(
        "Candidate search: user=%s job_title=%s location=%s sources=%s",
        user.email,
        job_title,
        location,
        source_list,
    )

    try:
        results = multi_source_search(
            job_title=job_title,
            location=location,
            must_have_skills=must_have_skills,
            good_to_have_skills=good_to_have_skills,
            num_results=min(num_results, 20),
            sources=source_list,
            find_emails=True,
        )

        xray = build_xray_query(
            job_title,
            location,
            must_have_skills,
            "linkedin",
        )

        return {
            "job_title": job_title,
            "location": location,
            "must_have_skills": must_have_skills,
            "good_to_have_skills": good_to_have_skills,
            "jd_text": jd_text,
            "xray_query": xray,
            "total_found": results.get("total_found", 0),
            "profiles": results.get("candidates", []),
            "stats": {
                "linkedin": results.get("linkedin_count", 0),
                "github": results.get("github_count", 0),
                "web": results.get("web_count", 0),
                "emails_found": results.get("emails_found", 0),
            },
            "error": results.get("error"),
        }

    except Exception as e:
        logger.exception("Candidate search failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xray-query")
def get_xray_query(
    job_title: str,
    token: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    db: Session = Depends(get_db),
):
    user = get_current_user(token, db)

    try:
        query = build_xray_query(
            job_title,
            location,
            must_have_skills,
            "linkedin",
        )

        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        logger.info("Generated X-Ray query for user=%s", user.email)

        return {
            "xray_query": query,
            "google_search_url": google_url,
            "instructions": "Copy the query and search on Google, or click the URL.",
        }

    except Exception as e:
        logger.exception("X-Ray query generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/find-email")
def find_email(
    name: str,
    company_domain: str = "",
    token: str = "",
    db: Session = Depends(get_db),
):
    if token:
        get_current_user(token, db)

    try:
        email = find_email_hunter(name, company_domain)

        return {
            "name": name,
            "company_domain": company_domain,
            "email": email,
            "found": bool(email),
            "powered_by": "Hunter.io",
        }

    except Exception as e:
        logger.exception("Hunter email lookup failed")
        raise HTTPException(status_code=500, detail=str(e))