from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

# ─── Configure Gemini ─────────────────────────
# Get free API key from: aistudio.google.com
load_dotenv()

GEMINI_API_KEY = "AIzaSyCCrMsDmHdlU_FFzt8V_jwrhHTmpi5Jv60"
client = genai.Client(api_key=GEMINI_API_KEY)

def score_resume_against_jd(jd_text: str, resume_text: str,
                              candidate_name: str = "Candidate") -> dict:
    """
    Score a resume against a job description using Gemini AI
    Returns score 0-100 with detailed analysis
    """

    prompt = f"""
You are an expert technical recruiter. Analyze this resume against the job description.

JOB DESCRIPTION:
{jd_text}

CANDIDATE RESUME:
{resume_text}

Provide a detailed analysis in this EXACT JSON format (no other text):
{{
    "candidate_name": "{candidate_name}",
    "overall_score": <number 0-100>,
    "match_percentage": <number 0-100>,
    "skills_matched": ["skill1", "skill2"],
    "skills_missing": ["skill1", "skill2"],
    "experience_match": "<Excellent/Good/Fair/Poor>",
    "education_match": "<Excellent/Good/Fair/Poor>",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "interview_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?"
    ],
    "recommendation": "<Highly Recommended/Recommended/Maybe/Not Recommended>",
    "summary": "<2-3 sentence summary>"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text.strip()

        # Clean response — remove markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
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
            "summary": f"Error analyzing resume: {str(e)}"
        }


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """
    Score multiple resumes and return ranked list
    resumes = [{"name": "John", "text": "resume text..."}, ...]
    """
    results = []

    for resume in resumes:
        score = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=resume["name"]
        )
        results.append(score)

    # Sort by overall_score descending
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Add rank
    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results