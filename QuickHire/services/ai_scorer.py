from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
import json
import time

# Ensure your client initialization targeting settings is correct
client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
]

# 1. Enforce strict type structures using a Pydantic Model Schema
class CandidateEvaluation(BaseModel):
    candidate_name: str
    overall_score: int = Field(description="Integer rating between 0 and 100")
    match_percentage: int = Field(description="Integer percentage between 0 and 100")
    skills_matched: List[str] = Field(description="Array listing at least 3 matching technical skills")
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
    """Score a resume against JD using modern Gemini 2.5 Flash architecture"""

    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": [],
            "skills_missing": [],
            "experience_match": "Poor",
            "education_match": "Poor",
            "strengths": [],
            "weaknesses": ["Could not read resume content"],
            "interview_questions": [],
            "recommendation": "Not Recommended",
            "summary": "Resume content could not be extracted properly."
        }

    prompt = f"""
You are an expert technical recruiter. Analyze this resume against the job description.Score STRICTLY out of 100 (not 10). Use the full range 0-100.

IMPORTANT: You MUST return a valid JSON object with ALL fields filled. No empty arrays allowed.

JOB DESCRIPTION:
{jd_text[:2000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Return ONLY this JSON with ALL fields populated (no markdown, no extra text):
{{
    "candidate_name": "{candidate_name}",
    "overall_score": <integer 0-100>,
    "match_percentage": <integer 0-100>,
    "skills_matched": ["list", "at", "least", "3", "skills", "from", "resume"],
    "skills_missing": ["list", "skills", "in", "JD", "not", "in", "resume"],
    "experience_match": "Excellent",
    "education_match": "Good",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "interview_questions": [
        "Specific question 1 based on their experience?",
        "Specific question 2 about a skill gap?",
        "Specific question 3 about their background?"
    ],
    "recommendation": "Highly Recommended",
    "summary": "Write 2-3 sentences summarizing this candidate's fit for the role."
}}

Rules:
- overall_score must be between 0-100
- skills_matched must have at least 3 items if candidate has any relevant skills
- experience_match must be one of: Excellent, Good, Fair, Poor
- education_match must be one of: Excellent, Good, Fair, Poor  
- recommendation must be one of: Highly Recommended, Recommended, Maybe, Not Recommended
- summary must be at least 2 sentences
- NEVER return empty arrays for skills_matched or skills_missing
"""

    try:
        # Hardcoding the direct active generation model explicitly
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        response_text = response.text.strip()

        # Clean markdown wrappers if present
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0]
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        result["candidate_name"] = candidate_name
        return result

    except Exception as e:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": [],
            "skills_missing": [],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": [],
            "weaknesses": [],
            "interview_questions": [],
            "recommendation": "Error",
            "summary": f"AI scoring failed to run model: {str(e)}"
        }

def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score multiple resumes and return ranked list of candidates"""
    results = []

    for i, resume in enumerate(resumes):
        print(f"Processing candidate profile evaluation {i+1}/{len(resumes)}", flush=True)
        candidate_current_name = resume.get("name", "Unknown")

        if not resume.get("text") or len(resume.get("text", "").strip()) < 30:
            results.append({
                "candidate_name": resume.get("name", "Unknown"),
                "overall_score": 0,
                "match_percentage": 0,
                "skills_matched": [],
                "skills_missing": [],
                "experience_match": "Could not read",
                "education_match": "Could not read",
                "strengths": [],
                "weaknesses": ["Resume content could not be extracted"],
                "interview_questions": [],
                "recommendation": "Not Recommended",
                "summary": "Could not extract text from this resume."
            })
            continue

        score = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=candidate_current_name
        )
        result["candidate_name"] = candidate_current_name

        # Ensure no empty fields
        if not result.get("skills_matched"):
            result["skills_matched"] = ["No specific skills identified"]
        if not result.get("skills_missing"):
            result["skills_missing"] = ["No major gaps identified"]
        if not result.get("experience_match"):
            result["experience_match"] = "Fair"
        if not result.get("education_match"):
            result["education_match"] = "Fair"
        if not result.get("strengths"):
            result["strengths"] = ["Relevant matching background"]
        if not result.get("interview_questions"):
            result["interview_questions"] = [
                "Tell me about your most relevant experience for this role?",
                "What is your strongest technical skill?",
                "Where do you see yourself improving?"
            ]
        if not result.get("summary"):
            result["summary"] = f"{candidate_current_name} is a candidate being evaluated for this position."

        results.append(result)

        # Sort array by final evaluated values
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Add ranks
    for i, result in enumerate(results):
        result["rank"] = i + 1

        return results

    # Sort by score
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Add ranks
    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results