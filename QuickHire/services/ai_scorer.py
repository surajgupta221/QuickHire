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


def _build_prompt(jd_text: str, resume_text: str, candidate_name: str, must_have_skills: str = "", good_to_have_skills: str = "") -> str:
    """Build strict AI scoring prompt"""
    must_section = f"""
⚠️ MUST HAVE SKILLS (mandatory — if missing, cap score at 35):
{must_have_skills}
""" if must_have_skills.strip() else ""

    good_section = f"""
✅ GOOD TO HAVE SKILLS (bonus if present):
{good_to_have_skills}
""" if good_to_have_skills.strip() else ""

    return f"""You are a strict resume-to-JD screening engine for hiring teams..
{must_section}{good_section}

JOB DESCRIPTION:
{jd_text[:3000]}

CANDIDATE: {candidate_name}
RESUME:
{resume_text[:4000]}

CRITICAL: If ANY must-have skill is missing from resume, overall_score MUST be 35 or below.

STRICT RULES:
1. Score only explicit evidence in resume — do not infer skills
2. If core required stack missing, cap score at 20
3. If resume is generic without project depth, cap at 30
4. If resume matches role title but not stack, cap at 40
5. Only award 80+ when 80% of must-have skills explicitly proven
6. Location/relocation mismatch = heavy penalty

SCORING MODEL (start at 100, subtract penalties):
- Required primary stack missing: -25 each
- Required secondary skill missing: -10 each
- No recent hands-on evidence: -15
- Wrong domain/role type: -15 to -25
- Generic project descriptions: -10 to -20
- Location mismatch: -15

RANKING: 0-20=reject, 21-30=weak, 31-50=partial, 51-70=moderate, 71-85=strong, 86-100=exceptional

Return ONLY this JSON — no markdown, no explanation, no apologies, no disclaimers, no filler text:
{{
    "candidate_name": "{candidate_name}",
    "overall_score": 0,
    "match_percentage": 0,
    "must_have_matched": ["must-have skills found in resume"],
    "must_have_missing": ["must-have skills NOT in resume"],
    "skills_matched": ["explicit skill from resume matching JD"],
    "skills_missing": ["required JD skill not in resume"],
    "experience_match": "Good",
    "education_match": "Good",
    "strengths": ["specific project evidence from resume", "relevant domain experience", "strong education background", "clear career progression"],
    "weaknesses": ["specific technical gap", "lack of project depth", "location mismatch", "generic resume statements"],
    "interview_questions": [
        "Question targeting core experience?",
        "Question about specific project mentioned?",
        "Question testing technical depth?",
        "Question targeting skill gap?",
        "System design or architecture question?"
    ],
    "recommendation": "Recommended",
    "summary": "Sentence 1: Core match justification. Sentence 2: Standout value or gap. Sentence 3: Hiring verdict. Sentence 4: Interview recommendation. Sentence 5: Any red flags or final notes."
}}

DECISION LOGIC:
- Core mandatory stack missing = cannot be Recommended or Highly Recommended
- Resume lacks project depth = reduce score sharply
- Exaggerated or vague claims = treat conservatively
- If must-have skills missing: max score = 35
- overall_score and match_percentage must be integers 0-100
- experience_match: exactly Excellent/Good/Fair/Poor
- education_match: exactly Excellent/Good/Fair/Poor  
- recommendation: exactly Highly Recommended/Recommended/Maybe/Not Recommended
- interview_questions: exactly 5 specific questions
- summary: exactly 5 sentences"""


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
    """Score using Groq AI as fallback"""
    if not groq_client or not GROQ_AVAILABLE:
        raise Exception("Groq not configured")

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert recruiter. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=2000
    )
    text = response.choices[0].message.content.strip()
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

    if not result.get("skills_matched"):
        result["skills_matched"] = ["General technical skills"]
    if not result.get("skills_missing"):
        result["skills_missing"] = ["Needs further assessment"]
    if not result.get("strengths"):
        result["strengths"] = ["Relevant background for the role"]
    if not result.get("weaknesses"):
        result["weaknesses"] = ["Further evaluation recommended"]
    if not result.get("interview_questions") or len(result["interview_questions"]) < 3:
        result["interview_questions"] = [
            "Tell me about your most relevant experience?",
            "What is your strongest technical skill?",
            "How do you approach learning new technologies?",
            "Describe a challenging project you worked on?",
            "How do you handle tight deadlines?"
        ]
    if not result.get("summary"):
        result["summary"] = (
            f"{candidate_name} has been evaluated against the job requirements. "
            f"Please review the detailed breakdown above. "
            f"Consider scheduling an interview to assess further."
            f" Note: Automated screening is a preliminary step and should be complemented with human judgment."
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
            "Contact support if issue persists",
            "Verify resume file is readable",
            "Try with a different file format"
        ],
        "recommendation": "Error",
        "summary": (
            f"Automated evaluation could not complete for {candidate_name}. "
            f"Please retry the screening process. "
            f"If the issue persists, contact support."
        )
    }


def apply_percentile_tiers(results: list) -> list:
    """Assign tier categories based on score percentile"""
    total = len(results)
    if total == 0:
        return results

    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        position_percentile = (idx / total) * 100
        if position_percentile <= 20:
            item["tier_category"] = "⭐ Top 20% (Elite Tier)"
        elif position_percentile <= 50:
            item["tier_category"] = "📈 Mid 30% (Strong Tier)"
        else:
            item["tier_category"] = "📋 Rest 50% (Standard Tier)"
        item["rank"] = idx + 1

    return results


def score_resume_against_jd(
    jd_text: str,
    resume_text: str,
    candidate_name: str = "Candidate",
    must_have_skills: str = "",
    good_to_have_skills: str = ""
) -> dict:
    """Score resume — Groq first, Gemini as fallback"""

    if not resume_text or len(resume_text.strip()) < 50:
        return _error_result(candidate_name, "Resume too short or empty")

    prompt = _build_prompt(jd_text, resume_text, candidate_name, must_have_skills, good_to_have_skills)

    # Try Groq first
    try:
        result = _score_with_groq(prompt, candidate_name)
        return _validate_result(result, candidate_name)
    except Exception as groq_error:
        error_str = str(groq_error)
        print(f"❌ Groq failed for {candidate_name}: {error_str[:100]}", flush=True)
        print(f"🔄 Trying Gemini fallback for {candidate_name}...", flush=True)

    # Fallback to Gemini
    try:
        result = _score_with_gemini(prompt, candidate_name)
        return _validate_result(result, candidate_name)
    except Exception as gemini_error:
        print(f"⚠️ Gemini also failed for {candidate_name}: {gemini_error}", flush=True)
        return _error_result(
            candidate_name,
            f"Groq: {str(groq_error)[:30]} | Gemini: {str(gemini_error)[:30]}"
        )


def process_single_resume(args) -> dict:
    """Worker for thread pool"""
    jd_text, resume, idx, total, must_have, good_to_have = args
    name = resume.get("name", f"Candidate {idx+1}")
    text = resume.get("text", "")
    print(f"Processing {idx+1}/{total}: {name}", flush=True)
    return score_resume_against_jd(jd_text, text, name, must_have, good_to_have)


def score_multiple_resumes(jd_text: str, resumes: list, must_have_skills: str = "", good_to_have_skills: str = "") -> list:
    """Score all resumes in parallel"""
    results = []
    MAX_WORKERS = 4

    tasks = [
        (jd_text, resume, idx, len(resumes), must_have_skills, good_to_have_skills)
        for idx, resume in enumerate(resumes)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {
            executor.submit(process_single_resume, task): task
            for task in tasks
        }

        for future in concurrent.futures.as_completed(future_to_task, timeout=120):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Thread failed: {str(e)}", flush=True)
                task_data = future_to_task[future]
                results.append(
                    _error_result(task_data[1].get("name", "Unknown"), str(e))
                )

    # Apply percentile tiers
    results = apply_percentile_tiers(results)
    return results