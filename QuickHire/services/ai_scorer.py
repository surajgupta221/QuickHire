from google import genai
from google.genai import types
from config import settings
import json
import concurrent.futures
import time
import os

# ─── Gemini Client ────────────────────────────
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ─── Groq Client (fallback) ───────────────────
try:
    from groq import Groq
    groq_key = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    groq_client = Groq(api_key=groq_key)
    GROQ_AVAILABLE = bool(groq_key)
except ImportError:
    groq_client = None
    GROQ_AVAILABLE = False


def _build_prompt(jd_text: str, resume_text: str, candidate_name: str) -> str:
    return f"""You are an expert technical recruiter. Analyze this resume against the job description.

JOB DESCRIPTION:
{jd_text[:1500]}

CANDIDATE: {candidate_name}
RESUME:
{resume_text[:2500]}

Return ONLY valid JSON. No markdown wrappers. No explanations. Just this exact JSON structure:
{{
    "candidate_name": "{candidate_name}",
    "overall_score": 75,
    "match_percentage": 70,
    "skills_matched": ["Python", "FastAPI", "REST APIs"],
    "skills_missing": ["Docker", "Kubernetes"],
    "experience_match": "Good",
    "education_match": "Good",
    "strengths": ["Strong Python background", "API development experience"],
    "weaknesses": ["Limited cloud experience"],
    "interview_questions": [
        "Describe your most complex Python project?",
        "How have you handled API authentication?",
        "What databases have you worked with?"
    ],
    "recommendation": "Recommended",
    "summary": "Candidate matches core requirements. Minor gaps in DevOps exposure."
}}

Rules:
- overall_score: integer 0-100
- match_percentage: integer 0-100  
- experience_match: exactly one of Excellent/Good/Fair/Poor
- education_match: exactly one of Excellent/Good/Fair/Poor
- recommendation: exactly one of Highly Recommended/Recommended/Maybe/Not Recommended"""


def _score_with_gemini(prompt: str, candidate_name: str) -> dict:
    """Score using Gemini AI"""
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    text = response.text.strip()
    return json.loads(text)


def _score_with_groq(prompt: str, candidate_name: str) -> dict:
    """Score using Groq AI as fallback"""
    if not groq_client or not GROQ_AVAILABLE:
        raise Exception("Groq not configured in environment parameters")

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", # 👈 Upgraded to 70B for bulletproof recruitment validation
        messages=[
            {
                "role": "system",
                "content": "You are an expert recruiter assistant. Always respond with raw, valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}, # 👈 Enforces valid JSON natively
        temperature=0.1,
        max_tokens=2000
    )
    text = response.choices[0].message.content.strip()
    return json.loads(text)


def _validate_result(result: dict, candidate_name: str) -> dict:
    """Ensure all required fields exist and are valid"""
    result["candidate_name"] = candidate_name

    if not isinstance(result.get("overall_score"), (int, float)):
        result["overall_score"] = 50
    if not isinstance(result.get("match_percentage"), (int, float)):
        result["match_percentage"] = 50

    result["overall_score"] = max(0, min(100, int(result["overall_score"])))
    result["match_percentage"] = max(0, min(100, int(result["match_percentage"])))

    valid_exp = ["Excellent", "Good", "Fair", "Poor"]
    if result.get("experience_match") not in valid_exp:
        result["experience_match"] = "Fair"
    if result.get("education_match") not in valid_exp:
        result["education_match"] = "Fair"

    valid_rec = ["Highly Recommended", "Recommended", "Maybe", "Not Recommended"]
    if result.get("recommendation") not in valid_rec:
        result["recommendation"] = "Maybe"

    # Fill default list fields if missing
    for field in ["skills_matched", "skills_missing", "strengths", "weaknesses", "interview_questions"]:
        if not result.get(field) or not isinstance(result[field], list) or len(result[field]) == 0:
            result[field] = ["Assessment pending review"]

    if not result.get("summary"):
        result["summary"] = f"{candidate_name} has been successfully parsed and evaluated."

    return result


def _error_result(candidate_name: str, error: str) -> dict:
    """Return structured error when all AI services fail"""
    return {
        "candidate_name": candidate_name,
        "overall_score": 0,
        "match_percentage": 0,
        "skills_matched": ["AI evaluation unavailable"],
        "skills_missing": ["AI evaluation unavailable"],
        "experience_match": "Poor",
        "education_match": "Poor",
        "strengths": ["Please retry screening"],
        "weaknesses": [f"Evaluation failed: {error[:60]}"],
        "interview_questions": ["Please check your API key quota configurations and retry"],
        "recommendation": "Maybe",
        "summary": f"Automated structural evaluation could not complete for {candidate_name} due to system constraints."
    }


def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate"
) -> dict:
    """Score resume with Groq first, fallback to Gemini if quota exceeded"""

    if not resume_text or len(resume_text.strip()) < 50:
        return _error_result(candidate_name, "Resume too short or empty")

    prompt = _build_prompt(jd_text, resume_text, candidate_name)

    # ─── 1st Try: Primary Execution via Groq ─────────────────────
    try:
        result = _score_with_groq(prompt, candidate_name)
        return _validate_result(result, candidate_name)
    except Exception as groq_error:
        error_str = str(groq_error)
        print(f"❌ Groq failed for {candidate_name}: {error_str[:100]}", flush=True)

        # ─── 2nd Try: Fallback to Gemini ─────────────────────
        print(f"🔄 Activating Gemini fallback pipeline for {candidate_name}...", flush=True)
        try:
            result = _score_with_gemini(prompt, candidate_name)
            return _validate_result(result, candidate_name)
        except Exception as gemini_error:
            print(f"⚠️ Gemini fallback also failed for {candidate_name}: {gemini_error}", flush=True)
            return _error_result(candidate_name, f"Groq: {error_str[:30]} | Gemini: {str(gemini_error)[:30]}")


def process_single_resume(args) -> dict:
    """Worker task mapping structure for our thread pool executor"""
    jd_text, resume, idx, total = args
    name = resume.get("name", f"Candidate #{idx+1}")
    text = resume.get("text", "")
    return score_resume_against_jd(jd_text, text, name)


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Parallel AI screening queue layer"""
    results = []
    MAX_WORKERS = 4  # Concurrently process 4 resumes at a time to prevent server socket timeouts

    tasks = [(jd_text, resume, idx, len(resumes)) for idx, resume in enumerate(resumes)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_resume = {executor.submit(process_single_resume, task): task for task in tasks}

        for future in concurrent.futures.as_completed(future_to_resume, timeout=120):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Thread execution failed: {str(e)}", flush=True)
                task_data = future_to_resume[future]
                results.append(_error_result(task_data[1].get("name", "Unknown"), str(e)))

    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results
