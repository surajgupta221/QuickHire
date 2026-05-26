from google import genai
from google.genai import types
from groq import Groq

from pydantic import BaseModel, Field
from typing import List

from config import settings

import json
import concurrent.futures
import time

# =========================
# CLIENTS
# =========================

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

groq_client = Groq(
    api_key=settings.GROQ_API_KEY
)

# =========================
# SCHEMA
# =========================

class CandidateEvaluation(BaseModel):
    candidate_name: str
    overall_score: int
    match_percentage: int
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
# FALLBACK
# =========================

def fallback_response(candidate_name, msg):

    return {
        "candidate_name": candidate_name,
        "overall_score": 0,
        "match_percentage": 0,
        "skills_matched": ["Parsing failure fallback"],
        "skills_missing": ["Parsing failure fallback"],
        "experience_match": "Error",
        "education_match": "Error",
        "strengths": [],
        "weaknesses": [msg],
        "interview_questions": [],
        "recommendation": "Maybe",
        "summary": msg
    }


# =========================
# SAFE JSON PARSER
# =========================

def normalize_result(data, candidate_name):

    data.setdefault("candidate_name", candidate_name)
    data.setdefault("overall_score", 0)
    data.setdefault("match_percentage", 0)
    data.setdefault("skills_matched", [])
    data.setdefault("skills_missing", [])
    data.setdefault("experience_match", "Fair")
    data.setdefault("education_match", "Fair")
    data.setdefault("strengths", [])
    data.setdefault("weaknesses", [])
    data.setdefault("interview_questions", [])
    data.setdefault("recommendation", "Maybe")
    data.setdefault("summary", "Evaluation complete.")

    return data


# =========================
# GEMINI SCORING
# =========================

def gemini_score(prompt, candidate_name):

    try:

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateEvaluation,
                temperature=0.2
            )
        )

        if not response.text:
            raise Exception("Empty Gemini response")

        parsed = json.loads(response.text)

        return normalize_result(parsed, candidate_name)

    except Exception as e:

        print(f"GEMINI FAILED: {e}")

        return None


# =========================
# GROQ FALLBACK
# =========================

def groq_score(prompt, candidate_name):

    try:

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = completion.choices[0].message.content

        # Clean markdown
        content = content.replace("```json", "")
        content = content.replace("```", "")

        parsed = json.loads(content)

        return normalize_result(parsed, candidate_name)

    except Exception as e:

        print(f"GROQ FAILED: {e}")

        return fallback_response(
            candidate_name,
            str(e)
        )


# =========================
# MAIN SINGLE SCORING
# =========================

def score_resume_against_jd(
    jd_text,
    resume_text,
    candidate_name="Candidate"
):

    if not resume_text or len(resume_text.strip()) < 50:

        return fallback_response(
            candidate_name,
            "Resume content too small"
        )

    prompt = f"""
You are an expert technical recruiter.

Evaluate candidate against job description.

Return STRICT JSON ONLY.

Required keys:
candidate_name
overall_score
match_percentage
skills_matched
skills_missing
experience_match
education_match
strengths
weaknesses
interview_questions
recommendation
summary

JOB DESCRIPTION:
{jd_text[:2000]}

RESUME:
{resume_text[:4000]}
"""

    # 1st Try Gemini
    gemini_result = gemini_score(
        prompt,
        candidate_name
    )

    if gemini_result:
        return gemini_result

    # 2nd Try Groq
    return groq_score(
        prompt,
        candidate_name
    )


# =========================
# MULTI THREAD
# =========================

def process_resume(args):

    jd_text, resume = args

    candidate_name = resume.get(
        "name",
        "Unknown"
    )

    try:

        return score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume.get("text", ""),
            candidate_name=candidate_name
        )

    except Exception as e:

        return fallback_response(
            candidate_name,
            str(e)
        )


# =========================
# BULK PROCESSING
# =========================

def score_multiple_resumes(
    jd_text,
    resumes
):

    results = []

    # IMPORTANT
    # 20 resumes stable

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        tasks = [
            (jd_text, resume)
            for resume in resumes
        ]

        futures = [
            executor.submit(
                process_resume,
                task
            )
            for task in tasks
        ]

        for future in concurrent.futures.as_completed(futures):

            try:

                result = future.result(timeout=90)

                results.append(result)

            except Exception as e:

                print("THREAD ERROR:", e)

    # SORTING

    results.sort(
        key=lambda x: x.get(
            "overall_score",
            0
        ),
        reverse=True
    )

    # RANKING

    for idx, item in enumerate(results):

        item["rank"] = idx + 1

    return results