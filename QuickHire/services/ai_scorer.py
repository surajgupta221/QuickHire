from google import genai
from google.genai import types
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

JOB DESCRIPTION:
{jd_text[:2000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Respond with ONLY this JSON — no other text, no markdown:
{{
    "candidate_name": "{candidate_name}",
    "overall_score": <number strictly between 0-100>,
    "match_percentage": <number strictly between 0-100>,
    ...rest of fields
}}
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
    """Score multiple resumes and return ranked list"""
    results = []

    for i, resume in enumerate(resumes):
        print(f"Processing candidate profile evaluation {i+1}/{len(resumes)}", flush=True)

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
            candidate_name=resume["name"]
        )
        results.append(score)

        # Small delay only if not last resume
        if i < len(resumes) - 1:
            time.sleep(1)  # Reduced from 4 to 1 second

    # Sort by score
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Add ranks
    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results

