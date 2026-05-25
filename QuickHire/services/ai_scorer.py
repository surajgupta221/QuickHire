from google import genai
from google.genai import types
from config import settings
import json
import time

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate"
) -> dict:
    """Score a resume against JD using Gemini AI"""

    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Could not read resume"],
            "skills_missing": ["N/A"],
            "experience_match": "Poor",
            "education_match": "Poor",
            "strengths": ["N/A"],
            "weaknesses": ["Could not read resume content"],
            "interview_questions": ["Please provide a readable resume"],
            "recommendation": "Not Recommended",
            "summary": "Resume content could not be extracted properly."
        }

    prompt = f"""
You are an expert technical recruiter. Analyze this resume against the job description.
Score STRICTLY out of 100. Use the full range 0-100.

JOB DESCRIPTION:
{jd_text[:2000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Return ONLY valid JSON with ALL fields populated. No markdown. No extra text:
{{
    "candidate_name": "{candidate_name}",
    "overall_score": <integer 0-100>,
    "match_percentage": <integer 0-100>,
    "skills_matched": ["skill1", "skill2", "skill3"],
    "skills_missing": ["missing1", "missing2"],
    "experience_match": "Excellent",
    "education_match": "Good",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "interview_questions": [
        "Question 1 based on experience?",
        "Question 2 about skill gap?",
        "Question 3 about background?"
    ],
    "recommendation": "Highly Recommended",
    "summary": "2-3 sentences about this candidate fit for the role."
}}

Rules:
- overall_score must be integer 0-100
- skills_matched must have minimum 3 items
- skills_missing must have minimum 2 items
- experience_match must be: Excellent, Good, Fair, or Poor
- education_match must be: Excellent, Good, Fair, or Poor
- recommendation must be: Highly Recommended, Recommended, Maybe, or Not Recommended
- summary must be minimum 2 sentences
- ALL arrays must have at least 1 item
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        response_text = response.text.strip()

        # Clean markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Force correct candidate name
        result["candidate_name"] = candidate_name

        # Guarantee no empty fields
        if not result.get("skills_matched"):
            result["skills_matched"] = ["No specific skills identified"]
        if not result.get("skills_missing"):
            result["skills_missing"] = ["No major gaps identified"]
        if not result.get("experience_match"):
            result["experience_match"] = "Fair"
        if not result.get("education_match"):
            result["education_match"] = "Fair"
        if not result.get("strengths"):
            result["strengths"] = ["Relevant background for the role"]
        if not result.get("weaknesses"):
            result["weaknesses"] = ["Further assessment needed"]
        if not result.get("interview_questions"):
            result["interview_questions"] = [
                "Tell me about your most relevant experience?",
                "What is your strongest technical skill?",
                "Where do you see yourself improving?"
            ]
        if not result.get("summary"):
            result["summary"] = f"{candidate_name} is being evaluated for this position."

        return result

    except Exception as e:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Error processing resume"],
            "skills_missing": ["Error processing resume"],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": ["Could not evaluate"],
            "weaknesses": ["AI scoring failed"],
            "interview_questions": ["Please retry the screening"],
            "recommendation": "Error",
            "summary": f"AI scoring failed: {str(e)}"
        }


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score multiple resumes and return ranked list"""
    results = []

    for i, resume in enumerate(resumes):
        print(f"Processing candidate {i+1}/{len(resumes)}: {resume.get('name')}", flush=True)

        # Score this resume
        result = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume.get("text", ""),
            candidate_name=resume.get("name", f"Candidate {i+1}")
        )
        results.append(result)

        # Small delay between requests
        if i < len(resumes) - 1:
            time.sleep(2)

    # Sort by score highest first
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Add rank numbers
    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results