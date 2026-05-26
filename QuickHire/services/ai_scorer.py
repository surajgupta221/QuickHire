from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
import json
import os
import time

# Robust, localized imports to safeguard production runtime environments
try:
    from groq import Groq
    groq_api_key = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
    groq_client = Groq(api_key=groq_api_key) if groq_api_key else None
except ImportError:
    groq_client = None

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 1. Strict Pydantic Data Contract
class CandidateEvaluation(BaseModel):
    candidate_name: str
    overall_score: int = Field(description="Integer rating between 0 and 100")
    match_percentage: int = Field(description="Integer percentage between 0 and 100")
    skills_matched: List[str] = Field(description="Array listing matching technical skills")
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
    """Score a single resume using Gemini with a highly optimized Groq backoff retry loop"""

    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Empty document data"],
            "skills_missing": ["Empty document data"],
            "experience_match": "Poor",
            "education_match": "Poor",
            "strengths": [],
            "weaknesses": ["Could not read resume content"],
            "interview_questions": [],
            "recommendation": "Not Recommended",
            "summary": "Resume content could not be read properly."
        }

    prompt = f"""
You are an expert technical recruiter evaluating {candidate_name} against this job requirement.
Analyze the experience, education, and technical alignment carefully.

JOB DESCRIPTION:
{jd_text[:3000]}

CANDIDATE RESUME:
{resume_text[:3000]}
"""

    # 💡 Step A: Try Primary Run with Gemini Natively
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateEvaluation, 
                temperature=0.2
            )
        )
        return json.loads(response.text)

    except Exception as gemini_error:
        error_msg = str(gemini_error)
        print(f"⚠️ Gemini processing unavailable: {error_msg}. Routing to fallback...", flush=True)
        
        # 💡 Step B: Execute Groq Fallback Loop with Built-In Exponential Backoff Rest Blocks
        if groq_client:
            groq_attempts = 4
            backoff_delay = 8.0  # Safe window starting point to completely clear free RPM walls
            
            for attempt in range(groq_attempts):
                try:
                    print(f"🚀 [Groq Attempt {attempt+1}/{groq_attempts}] Processing evaluation for: {candidate_name}...", flush=True)
                    
                    groq_instruction = (
                        f"{prompt}\n\n"
                        "CRITICAL: Return ONLY a raw JSON object string. Do not wrap it in markdown block tags like ```json. "
                        "Do not add any prose text before or after the JSON structure. Match these schema keys exactly:\n"
                        "{\n"
                        '  "candidate_name": "string",\n'
                        '  "overall_score": 0,\n'
                        '  "match_percentage": 0,\n'
                        '  "skills_matched": ["string"],\n'
                        '  "skills_missing": ["string"],\n'
                        '  "experience_match": "string",\n'
                        '  "education_match": "string",\n'
                        '  "strengths": ["string"],\n'
                        '  "weaknesses": ["string"],\n'
                        '  "interview_questions": ["string"],\n'
                        '  "recommendation": "string",\n'
                        '  "summary": "string"\n'
                        "}"
                    )
                    
                    completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": groq_instruction}],
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    
                    raw_output = completion.choices.message.content.strip()
                    return json.loads(raw_output)
                    
                except Exception as groq_error:
                    print(f"⚠️ Groq rate ceiling limit or formatting issue hit: {groq_error}", flush=True)
                    if attempt < groq_attempts - 1:
                        print(f"⏳ Backing off pipeline logic... Sleeping for {backoff_delay} seconds.", flush=True)
                        time.sleep(backoff_delay)
                        backoff_delay *= 2.0  # Dynamic progressive backoff: 8s, 16s, 32s
                    else:
                        print(f"❌ All fallback computational recovery options completely exhausted for {candidate_name}.", flush=True)
        else:
            print("⚠️ Groq API client infrastructure unavailable. Moving forward...", flush=True)

        # Resilient structural fallback recovery dictionary
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Parsing failure fallback"],
            "skills_missing": ["Parsing failure fallback"],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": ["All active structural inference endpoints exhausted limits"],
            "weaknesses": ["System reached active account quota thresholds during processing"],
            "interview_questions": ["Could not parse sample evaluation paths"],
            "recommendation": "Maybe",
            "summary": f"Evaluation engine processing failed safely. Diagnostics trace: {error_msg}"
        }

def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Process multiple resumes sequentially while enforcing safe API pacing rules"""
    results = []

    for i, resume in enumerate(resumes):
        print(f"Processing candidate profile evaluation {i+1}/{len(resumes)}", flush=True)
        candidate_current_name = resume.get("name", "Unknown")

        if not resume.get("text") or len(resume.get("text", "").strip()) < 30:
            results.append({
                "candidate_name": candidate_current_name,
                "overall_score": 0,
                "match_percentage": 0,
                "skills_matched": ["Unreadable file layout"],
                "skills_missing": ["Unreadable file layout"],
                "experience_match": "Could not read",
                "education_match": "Could not read",
                "strengths": [],
                "weaknesses": ["Resume content could not be extracted"],
                "interview_questions": [],
                "recommendation": "Not Recommended",
                "summary": "Could not extract plain text from this document."
            })
            continue

        result = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=candidate_current_name
        )
        
        # Enforce property mapping normalization guarantees
        result["candidate_name"] = candidate_current_name

        if not result.get("skills_matched"):
            result["skills_matched"] = ["No specific skills identified"]
        if not result.get("skills_missing"):
            result["skills_missing"] = ["No major gaps identified"]
        if not result.get("experience_match"):
            result["experience_match"] = "Fair"
        if not result.get("education_match"):
            result["education_match"] = "Fair"
        if not result.get("strengths"):
            result["strengths"] = ["Relevant background profile"]
        if not result.get("weaknesses"):
            result["weaknesses"] = ["No major concerns found"]
        if not result.get("interview_questions"):
            result["interview_questions"] = ["Tell me about your technical background?"]
        if not result.get("summary"):
            result["summary"] = f"{candidate_current_name} evaluation complete."

        results.append(result)

        # 🕒 Crucial Step: Expanded Rate Limit Pacing Delay
        # To handle 20 resumes without hitting free tier RPM blocks, we enforce a strict 6-second rest block between candidates.
        if i < len(resumes) - 1:
            print("Pacing requests to respect platform API rate limits... Sleeping for 6 seconds.", flush=True)
            time.sleep(6.0)

    # Sort results sequentially by score ranking parameters
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results
