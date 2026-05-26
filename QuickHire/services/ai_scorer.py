from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
import json
import concurrent.futures
import time

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# =========================
# STRICT RESPONSE SCHEMA
# =========================
class CandidateEvaluation(BaseModel):
    candidate_name: str
    overall_score: int = Field(description="Integer rating between 0 and 100")
    match_percentage: int = Field(description="Integer percentage between 0 and 100")
    skills_matched: List[str]
    skills_missing: List[str]
    experience_match: str
    education_match: str
    strengths: List[str]
    weaknesses: List[str]
    interview_questions: List[str]
    recommendation: str
    summary: str


# =========================
# FALLBACK RESPONSE
# =========================
def fallback_response(candidate_name: str, error_msg: str):
    return {
        "candidate_name": candidate_name,
        "overall_score": 0,
        "match_percentage": 0,
        "skills_matched": ["Parsing failure fallback"],
        "skills_missing": ["Parsing failure fallback"],
        "experience_match": "Error",
        "education_match": "Error",
        "strengths": ["Failed to extract structural arrays"],
        "weaknesses": [error_msg],
        "interview_questions": ["Could not process questions"],
        "recommendation": "Maybe",
        "summary": error_msg
    }


# =========================
# SINGLE RESUME SCORING
# =========================
def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate"
) -> dict:

    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Empty document data"],
            "skills_missing": ["Empty document data"],
            "experience_match": "Poor",
            "education_match": "Poor",
            "strengths": [],
            "weaknesses": ["Could not read resume content"],
            "interview_questions": [],
            "recommendation": "Not Recommended",
            "summary": "Resume content could not be read properly."
        }

    prompt = f"""
You are an expert technical recruiter.

Evaluate the candidate strictly against the job description.

Return valid JSON only.

JOB DESCRIPTION:
{jd_text[:3000]}

CANDIDATE RESUME:
{resume_text[:5000]}
"""

    # Retry mechanism
    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CandidateEvaluation,
                    temperature=0.2
                )
            )

            # Safer parsing
            if not response.text:
                raise Exception("Empty Gemini response")

            parsed = json.loads(response.text)

            # Ensure required keys exist
            parsed.setdefault("candidate_name", candidate_name)
            parsed.setdefault("overall_score", 0)
            parsed.setdefault("match_percentage", 0)
            parsed.setdefault("skills_matched", [])
            parsed.setdefault("skills_missing", [])
            parsed.setdefault("experience_match", "Fair")
            parsed.setdefault("education_match", "Fair")
            parsed.setdefault("strengths", [])
            parsed.setdefault("weaknesses", [])
            parsed.setdefault("interview_questions", [])
            parsed.setdefault("recommendation", "Maybe")
            parsed.setdefault("summary", "Evaluation complete.")

            return parsed

        except Exception as e:
            print(f"Retry {attempt+1} failed for {candidate_name}: {e}")

            time.sleep(2)

            if attempt == 2:
                return fallback_response(
                    candidate_name,
                    f"Gemini processing failed: {str(e)}"
                )


# =========================
# MULTIPLE RESUME SCORING
# =========================
def process_single_resume(args):
    jd_text, resume = args

    candidate_current_name = resume.get("name", "Unknown")

    try:

        if not resume.get("text") or len(resume.get("text", "").strip()) < 30:
            return {
                "candidate_name": candidate_current_name,
                "overall_score": 0,
                "match_percentage": 0,
                "skills_matched": ["Unreadable file layout"],
                "skills_missing": ["Unreadable file layout"],
                "experience_match": "Could not read",
                "education_match": "Could not read",
                "strengths": [],
                "weaknesses": ["Resume content could not be extracted"],
                "interview_questions": [],
                "recommendation": "Not Recommended",
                "summary": "Could not extract plain text from this document."
            }

        result = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=candidate_current_name
        )

        result["candidate_name"] = candidate_current_name

        return result

    except Exception as e:
        return fallback_response(
            candidate_current_name,
            str(e)
        )


# =========================
# MAIN BULK SCORING
# =========================
def score_multiple_resumes(jd_text: str, resumes: list) -> list:

    results = []

    # Parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        tasks = [
            (jd_text, resume)
            for resume in resumes
        ]

        future_to_resume = {
            executor.submit(process_single_resume, task): task
            for task in tasks
        }

        for future in concurrent.futures.as_completed(future_to_resume):

            try:
                result = future.result(timeout=120)
                results.append(result)

            except Exception as e:
                print("Thread execution failed:", e)

    # Sort ranking
    results.sort(
        key=lambda x: x.get("overall_score", 0),
        reverse=True
    )

    # Add rank
    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results