import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services.auth import verify_token
from services.linkedin_search import search_linkedin_profiles, build_xray_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/linkedin", tags=["LinkedIn Search"])


def get_current_user(token: str, db: Session):
    logger.info("Validating token for current user")
    payload = verify_token(token)
    if not payload:
        logger.warning("Invalid token received")
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(
        User.email == payload.get("sub")
    ).first()
    if not user:
        logger.warning("User not found for token subject: %s", payload.get("sub"))
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Authenticated user: %s", user.email)
    return user


@router.get("/search")
def search_candidates(
    job_title: str,
    token: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    num_results: int = 10,
    db: Session = Depends(get_db)
):
    """Search LinkedIn profiles using Google X-Ray"""
    user = get_current_user(token, db)

    if user.screening_credits <= 0:
        logger.warning("User %s attempted search with no credits", user.email)
        raise HTTPException(
            status_code=403,
            detail="No credits left. Please upgrade your plan."
        )

    logger.info(
        "LinkedIn search request: user=%s job_title=%s location=%s must_have_skills=%s good_to_have_skills=%s num_results=%s",
        user.email, job_title, location, must_have_skills, good_to_have_skills, num_results
    )

    results = search_linkedin_profiles(
        job_title=job_title,
        location=location,
        must_have_skills=must_have_skills,
        good_to_have_skills=good_to_have_skills,
        num_results=min(num_results, 20)
    )

    return {
        "job_title": job_title,
        "location": location,
        "must_have_skills": must_have_skills,
        "xray_query": results.get("query"),
        "total_found": results.get("total_found", 0),
        "profiles": results.get("profiles", []),
        "error": results.get("error")
    }


@router.get("/xray-query")
def get_xray_query(
    job_title: str,
    token: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    db: Session = Depends(get_db)
):
    """Get the X-Ray search query without using credits"""
    user = get_current_user(token, db)

    query = build_xray_query(
        job_title, location,
        must_have_skills, good_to_have_skills
    )

    google_search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    logger.info("Generated X-Ray query for user=%s query=%s", user.email, query)

    return {
        "xray_query": query,
        "google_search_url": google_search_url,
        "instructions": "Copy the query and search on Google, or click the URL"
    }