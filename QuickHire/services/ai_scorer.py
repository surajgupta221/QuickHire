from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
import json
import time

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 1. Strict Pydantic Data Contract
class CandidateEvaluation(BaseModel):
    candidate_name: str
    overall_score: int = Field(description="Integer rating between 0 and 100")
    match_percentage: int = Field(description="Integer percentage between 0 and 100")
    skills_matched: List[str] = Field(description="Array listing matching technical skills")
    skills_missing: List[str] = Field(description="Array listing required job description skills missing from the resume")
    experience_match: str
    education_match: str
    strengths: List[str]
    weaknesses: List[str]
    interview_questions: List[str]
    recommendation: str
    summary: str

def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate"
) -> dict:
    """Score a single resume using Gemini Structured Output models"""

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
You are an expert technical recruiter evaluating {candidate_name} against this job requirement.
Analyze the experience, education, and technical alignment carefully.

JOB DESCRIPTION:
{jd_text[:2000]}

CANDIDATE RESUME:
{resume_text[:2000]}
"""

    try:
        # Enforcing structured schemas natively
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateEvaluation, # 👈 Enforces schema matching
                temperature=0.2
            )
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"⚠️ Gemini output block failed: {e}", flush=True)
        # Fully populated fallback dictionary matching the exact schema definition
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Parsing failure fallback"],
            "skills_missing": ["Parsing failure fallback"],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": ["Failed to extract structural arrays"],
            "weaknesses": ["Failed to extract structural arrays"],
            "interview_questions": ["Could not process questions"],
            "recommendation": "Maybe",
            "summary": f"Evaluation extraction ran into an unexpected system crash trace: {str(e)}"
        }

def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score multiple resumes and return ranked list of candidates"""
    results = []

    for i, resume in enumerate(resumes):
        print(f"Processing candidate profile evaluation {i+1}/{len(resumes)}", flush=True)
        candidate_current_name = resume.get("name", "Unknown")

        if not resume.get("text") or len(resume.get("text", "").strip()) < 30:
            results.append({
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
            })
            continue

        result = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=candidate_current_name
        )
        
        # Safe normalization assertions
        result["candidate_name"] = candidate_current_name

        if not result.get("skills_matched"):
            result["skills_matched"] = ["No specific skills identified"]
        if not result.get("skills_missing"):
            result["skills_missing"] = ["No major gaps identified"]
        if not result.get("experience_match"):
            result["experience_match"] = "Fair"
        if not result.get("education_match"):
            result["education_match"] = "Fair"
        if not result.get("strengths"):
            result["strengths"] = ["Relevant background profile"]
        if not result.get("weaknesses"):
            result["weaknesses"] = ["No major concerns found"]
        if not result.get("interview_questions"):
            result["interview_questions"] = ["Tell me about your technical background?"]
        if not result.get("summary"):
            result["summary"] = f"{candidate_current_name} evaluation complete."

        results.append(result)

    # ✅ FIXED INDENTATION: Loop completes fully, then arrays are sorted and ranked
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results
