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
    return f"""You are an elite corporate technical recruiter and talent assessor. 
Critically evaluate the candidate {candidate_name} against the provided Job Description.
Provide deeply analytical, specific, and impactful hiring metrics.

JOB DESCRIPTION:
{jd_text[:4000]}

CANDIDATE: {candidate_name}
RESUME:
{resume_text[:6000]}

Return ONLY valid JSON. No markdown wrappers. No explanations. 
CRITICAL: Do NOT copy the example scores (85 or 88). Calculate a unique, critical mathematical score based strictly on candidate alignment!

You are a strict resume-to-JD screening engine for hiring teams.

TASK
Compare the candidate resume against the job description and produce a JSON object only.
Your goal is to rank candidates conservatively and strictly. Do not be generous. Do not inflate scores. Use only explicit evidence from the resume and JD.

STRICT RULES
1. Score only what is explicitly supported by the resume text.
2. Do not infer skills, domain knowledge, or seniority from vague statements.
3. If a required skill is missing or unclear, count it as missing.
4. If the resume does not prove recent hands-on experience with a required stack, treat it as missing.
5. If location, relocation, work authorization, notice period, or shift compatibility are required and not explicitly matched, penalize heavily.
6. If the resume is generic, keyword-stuffed, or lacks project depth, cap the score at 30.
7. If the candidate lacks core JD stack alignment, cap the score at 20.
8. Only award high scores when the resume directly proves most required skills, relevant projects, and matching seniority.
9. Prefer precision over recall. False positives are worse than false negatives.
10. Return only valid JSON matching the schema. No markdown, no explanation.

SCORING MODEL
Start at 100 and subtract penalties.

Core technical alignment:
- Required primary stack missing: -25 each
- Required secondary skill missing: -10 each
- No evidence of hands-on use in last 2–3 years: -15
- Wrong role type or wrong domain: -15 to -25
- Weak or generic project descriptions: -10 to -20
- Missing measurable outcomes or technical ownership: -5 to -15

Operational fit:
- Location mismatch with no relocation proof: -15
- Relocation not mentioned when required: -10
- Notice period too long or absent when urgent hiring requires availability: -5 to -10
- Work authorization/onsite/shift mismatch if required: -10 to -20

Quality controls:
- If resume contains only course names, certifications, or tutorials without project evidence, cap score at 20.
- If resume shows unrelated experience with minimal overlap, cap score at 30.
- If resume matches role title but not the actual stack, cap score at 40.
- If resume matches stack and domain strongly, allow 70+.
- Do not give 80+ unless at least 80% of must-have items are explicitly proven.

RANKING BUCKETS
- 0–20 = reject
- 21–30 = weak match
- 31–50 = partial match
- 51–70 = moderate match
- 71–85 = strong match
- 86–100 = exceptional match

JSON OUTPUT RULES
- candidate_name: extract exact candidate name if available; otherwise "Unknown"
- overall_score: integer 0–100 after penalties
- match_percentage: integer 0–100; should be similar to overall_score but can be slightly lower if operational fit is weak
- skills_matched: only explicit technical stacks from resume that are directly relevant to JD
- skills_missing: only missing JD requirements or clear gaps
- experience_match: one of [Excellent, Good, Fair, Poor]
- education_match: one of [Excellent, Good, Fair, Poor]
- strengths: specific project-level strengths with evidence
- weaknesses: specific technical/architectural gaps
- interview_questions: exactly 5 questions, tailored to the gaps and resume claims
- recommendation: one of [Highly Recommended, Recommended, Maybe, Not Recommended]
- summary: exactly 3 sentences, professional and strict

DECISION LOGIC
- If core mandatory stack is missing, recommendation cannot be "Recommended" or "Highly Recommended".
- If location or relocation is a hard requirement and not proven, reduce recommendation by at least one level.
- If the resume lacks project depth, reduce overall_score sharply even if keywords appear.
- If the resume seems exaggerated or vague, treat claims conservatively.

OUTPUT FORMAT
Return only this JSON schema:
{
  "candidate_name": "",
  "overall_score": 0,
  "match_percentage": 0,
  "skills_matched": [],
  "skills_missing": [],
  "experience_match": "",
  "education_match": "",
  "strengths": [],
  "weaknesses": [],
  "interview_questions": [],
  "recommendation": "",
  "summary": ""
}

# Your response must strictly match this JSON schema structure:
# {{
#     "candidate_name": "{candidate_name}",
#     "overall_score": 0,
#     "match_percentage": 0,
#     "skills_matched": ["List distinct technical stacks matching the JD explicitly"],
#     "skills_missing": ["List missing technical skills or domain alignment gaps based on the JD"],
#     "experience_match": "Good",
#     "education_match": "Good",
#     "strengths": ["Identify unique, project-specific engineering achievements found in resume text"],
#     "weaknesses": ["Identify genuine technical limitations or architectural experience gaps"],
#     "interview_questions": [
#         "Easy question regarding core claimed experience",
#         "Medium problem-solving question regarding a mentioned project",
#         "Tough technical scenario question testing their specific stack",
#         "Question targeting an identified skill gap",
#         "Architectural or system design question based on past projects"
#     ],
#     "recommendation": "Recommended",
#     "summary": "Provide a comprehensive 3-sentence professional evaluation. Sentence 1: Core match justification. Sentence 2: Standout value proposition. Sentence 3: Definitive hiring verdict."
# }}

# Strict Data Rules:
# - overall_score: Calculate a realistic dynamic integer between 0 and 100 based strictly on technical alignment.
# - match_percentage: Calculate a realistic dynamic integer between 0 and 100 based strictly on technical alignment.
# - Do not return generic phrases like 'Relevant experience'. Be hyper-specific to their resume text.
# - experience_match: must be exactly one of [Excellent, Good, Fair, Poor]
# - education_match: must be exactly one of [Excellent, Good, Fair, Poor]
# - recommendation: must be exactly one of [Highly Recommended, Recommended, Maybe, Not Recommended]
# - interview_questions: must contain exactly 5 specific questions matching the schema array length.
# - summary: minimum 3 complete sentences."""

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
        "recommendation": "Error",
        "summary": f"Automated evaluation could not complete for {candidate_name}. Please retry."
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

        # Check if quota exceeded
        is_quota_error = any(x in error_str for x in [
            "429", "RESOURCE_EXHAUSTED", "quota", "rate limit"
        ])

        if is_quota_error:
            print(f"🔄 Quota exceeded, trying Gemini for {candidate_name}...", flush=True)
        else:
            print(f"🔄 Groq error, trying Gemini for {candidate_name}...", flush=True)


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

def apply_percentile_tiers(results: list) -> list:
    """Categorizes candidates dynamically into elite recruitment percentiles based on total batch size"""
    total = len(results)
    if total == 0:
        return results

    # Sort candidates by overall score to rank them
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        # Calculate individual rank position percentage
        position_percentile = (idx / total) * 100

        if position_percentile <= 20:
            item["tier_category"] = "⭐ Top 20% (Elite Tier)"
        elif position_percentile <= 50:
            item["tier_category"] = "📈 Mid 30% (Strong Tier)"
        else:
            item["tier_category"] = "📋 Rest 50% (Standard Tier)"
            
        item["rank"] = idx + 1
        
    results = apply_percentile_tiers(results)
    return results


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
