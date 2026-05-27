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
    # Fallback checking both config settings object parameters and raw OS environments
    groq_key = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    groq_client = Groq(api_key=groq_key)
    GROQ_AVAILABLE = bool(groq_key)
except ImportError:
    groq_client = None
    GROQ_AVAILABLE = False


def _build_prompt(jd_text: str, resume_text: str, candidate_name: str) -> str:
    return f"""You are an expert technical recruiter. Analyze this resume against the job description.

JOB DESCRIPTION:
{jd_text[:2500]}

CANDIDATE: {candidate_name}
RESUME:
{resume_text[:3500]}

Return ONLY valid JSON. No markdown wrappers. No explanation text block. Just this exact JSON schema:
{{
    "candidate_name": "{candidate_name}",
    "overall_score": 75,
    "match_percentage": 70,
    "skills_matched": ["Python", "FastAPI", "REST APIs"],
    "skills_missing": ["Docker", "Kubernetes"],
    "experience_match": "Good",
    "education_match": "Good",
    "strengths": ["Strong Python background", "API development experience", "Good problem solving"],
    "weaknesses": ["Limited cloud experience", "No DevOps exposure"],
    "interview_questions": [
        "Describe your most complex Python project?",
        "How have you handled API authentication and security?",
        "What databases have you worked with and how did you optimize queries?"
    ],
    "recommendation": "Recommended",
    "summary": "Strong candidate with relevant Python experience matching core requirements. Minor skill gaps in cloud technologies but overall good fit for the role."
}}

Rules:
- overall_score: integer 0-100
- match_percentage: integer 0-100  
- experience_match: exactly one of Excellent/Good/Fair/Poor
- education_match: exactly one of Excellent/Good/Fair/Poor
- recommendation: exactly one of Highly Recommended/Recommended/Maybe/Not Recommended
- skills_matched: minimum 3 real skills from resume
- skills_missing: minimum 2 skills from JD not in resume
- strengths: minimum 3 specific strengths
- interview_questions: exactly 3 specific questions
- summary: minimum 2 complete sentences"""


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
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    result = json.loads(text)
    print(f"✅ Gemini scored {candidate_name}: {result.get('overall_score')}/100", flush=True)
    return result


def _score_with_groq(prompt: str, candidate_name: str) -> dict:
    """Score using Groq AI as primary/secondary engine"""
    if not groq_client or not GROQ_AVAILABLE:
        raise Exception("Groq client initialization failure or missing GROQ_API_KEY config")

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", # 👈 Upgraded to 70B for bulletproof recruitment parsing
        messages=[
            {
                "role": "system",
                "content": "You are an expert technical recruiter assistant. Always respond with valid raw JSON structures matching the keys requested exactly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}, # 👈 Native JSON constraint protection
        temperature=0.1,
        max_tokens=2000
    )

    text = response.choices[0].message.content.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    result = json.loads(text)
    print(f"✅ Groq scored {candidate_name}: {result.get('overall_score')}/100", flush=True)
    return result


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

    if not result.get("skills_matched") or len(result["skills_matched"]) == 0:
        result["skills_matched"] = ["General technical skills"]
    if not result.get("skills_missing") or len(result["skills_missing"]) == 0:
        result["skills_missing"] = ["Specific requirements need assessment"]
    if not result.get("strengths") or len(result["strengths"]) == 0:
        result["strengths"] = ["Relevant background for the role"]
    if not result.get("weaknesses") or len(result["weaknesses"]) == 0:
        result["weaknesses"] = ["Further evaluation recommended"]
    if not result.get("interview_questions") or len(result["interview_questions"]) == 0:
        result["interview_questions"] = [
            "Tell me about your most relevant experience for this role?",
            "What is your strongest technical skill and how have you applied it?",
            "How do you approach learning new technologies?"
        ]
    if not result.get("summary"):
        result["summary"] = (
            f"{candidate_name} has been evaluated against the job requirements. "
            f"Please review the detailed breakdown above."
        )

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
        "weaknesses": [f"Evaluation failed: {error[:100]}"],
        "interview_questions": [
            "Please retry the screening process",
            "Check API quota and try again",
            "Contact support if issue persists"
        ],
        "recommendation": "Maybe",
        "summary": f"Automated evaluation could not complete for {candidate_name}. System tracing context: {error[:80]}"
    }


def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate"
) -> dict:
    """Score resume with Groq first, fallback to Gemini if rate limits occur"""

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

        # ─── 2nd Try: Fallback Execution via Gemini ──────────────────
        print(f"🔄 Activating Gemini fallback pipeline for {candidate_name}...", flush=True)
        try:
            gemini_result = _score_with_gemini(prompt, candidate_name)
            return _validate_result(gemini_result, candidate_name)
        except Exception as gemini_error:
            print(f"❌ Gemini fallback also failed for {candidate_name}: {gemini_error}", flush=True)
            # 💡 FIXED: Explicitly return the structural error block if both engines fail
            return _error_result(candidate_name, f"Groq Error: {error_str[:40]} | Gemini Error: {str(gemini_error)[:40]}")


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Process up to 20 resumes concurrently using multithreaded workers to prevent UI connection drop-offs"""
    results = []

    def _worker(resume_item):
        name = resume_item.get("name", "Unknown Candidate")
        text = resume_item.get("text", "")
        return score_resume_against_jd(jd_text, text, name)

    print(f"🚀 Launching concurrent evaluation cluster for {len(resumes)} resumes...", flush=True)
    
    # max_workers=4 processes batches efficiently without hitting API network socket ceilings
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_worker, r): r for r in resumes}
        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result(timeout=60)
                results.append(data)
            except Exception as e:
                orig_item = futures[future]
                fail_name = orig_item.get("name", "Unknown Candidate")
