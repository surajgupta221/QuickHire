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
            model="gemini-2.5-flash",  # 👈 Kept standard stable model line
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
        print(f"⚠️ GEMINI FAILED FOR {candidate_name}: {e}", flush=True)
        return None


# =========================
# GROQ FALLBACK
# =========================

def groq_score(prompt, candidate_name):
    try:
        # Add strict key configuration rules to the payload for safety
        groq_instruction = (
            f"{prompt}\n\n"
            "CRITICAL: Return ONLY a raw JSON object string matching this schema structure. "
            "Do not include any text before or after the JSON structure.\n"
        )

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.1,  # Lower temperature lowers hallucinations
            response_format={"type": "json_object"},  # 👈 FIXED: Forces Groq to output clean JSON structure
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise parsing assistant. Output ONLY valid JSON strings matching the exact schema keys requested."
                },
                {
                    "role": "user",
                    "content": groq_instruction
                }
            ]
        )

        content = completion.choices[0].message.content.strip()

        # Clean markdown wrappers out safely
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        return normalize_result(parsed, candidate_name)

    except Exception as e:
        print(f"❌ GROQ FALLBACK CRASHED FOR {candidate_name}: {e}", flush=True)
        return fallback_response(candidate_name, f"Both Gemini and Groq systems exhausted. Error: {str(e)}")


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
You are an expert technical recruiter. Evaluate candidate against job description.
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
{jd_text[:3000]}

RESUME:
{resume_text[:4000]}
"""

    # 1st Try Gemini
    gemini_result = gemini_score(prompt, candidate_name)
    if gemini_result:
        return gemini_result

    # 2nd Try Groq if Gemini hits a 429 limit wall
    print(f"🚀 Gemini blocked or limit hit. Routing {candidate_name} to Groq fallback layer...", flush=True)
    return groq_score(prompt, candidate_name)


# =========================
# MULTI THREAD
# =========================

def process_resume(args):
    jd_text, resume = args
    candidate_name = resume.get("name", "Unknown")

    try:
        return score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume.get("text", ""),
            candidate_name=candidate_name
        )
    except Exception as e:
        return fallback_response(candidate_name, str(e))


# =========================
# BULK PROCESSING
# =========================

def score_multiple_resumes(
    jd_text,
    resumes
):
    results = []

    # Max workers set to 4 to balance high volume execution without flooding network sockets
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [(jd_text, resume) for resume in resumes]
        
        # Submit all tasks immediately to kick off parallel processing cluster
        futures = {executor.submit(process_resume, task): task for task in tasks}

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception as e:
                task_data = futures[future]
                failed_name = task_data[1].get("name", "Unknown")
                print(f"❌ THREAD POOL WORKER ERROR for {failed_name}: {e}", flush=True)
                results.append(fallback_response(failed_name, f"Thread timeout error: {str(e)}"))

    # SORTING BY SCORE
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # RANKING GENERATION
    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results
