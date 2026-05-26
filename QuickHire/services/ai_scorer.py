from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
from concurrent.futures import ThreadPoolExecutor # 👈 Added for high-volume parallel execution
import json
import os

# Safe, dynamic setup for Groq engine fallback
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
    """Score a single resume using Gemini with an optimized text structural Groq fallback"""

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

    # 1. Attempt Primary Request with Gemini
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
        print(f"⚠️ Gemini Busy or Throttled for {candidate_name}. Routing to Groq...", flush=True)
        
        # 2. Automated Fallback Execution via Groq
        if groq_client:
            try:
                groq_instruction = (
                    f"{prompt}\n\n"
                    "CRITICAL: Respond ONLY with a raw JSON object string. Do not use markdown block tags like ```json. "
                    "Do not include any chat commentary. Match these dictionary keys exactly:\n"
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
                print(f"❌ Groq fallback engine also failed for {candidate_name}: {groq_error}", flush=True)
        else:
            print("⚠️ Groq API key config missing. Fallback engine skipped.", flush=True)

        # Fail-safe structural recovery dictionary matching the schema contract
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Parsing failure fallback"],
            "skills_missing": ["Parsing failure fallback"],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": ["Inference engine limits exceeded"],
            "weaknesses": ["System encountered network timeout constraints during bulk parsing"],
            "interview_questions": ["Could not process generation paths"],
            "recommendation": "Maybe",
            "summary": f"Evaluation crashed cleanly. Logs: {error_msg}"
        }

def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score up to 20 resumes concurrently using multithreading to eliminate HTTP timeouts"""
    results = []
    
    # Internal helper function to pass to our thread executor
    def process_single_candidate(resume):
        candidate_current_name = resume.get("name", "Unknown")
        
        if not resume.get("text") or len(resume.get("text", "").strip()) < 30:
            return {
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
            }
            
        result = score_resume_against_jd(
            jd_text=jd_text,
            resume_text=resume["text"],
            candidate_name=candidate_current_name
        )
        
        # Safe normalization normalization guarantees
        result["candidate_name"] = candidate_current_name
        if not result.get("skills_matched"): result["skills_matched"] = ["No specific skills identified"]
        if not result.get("skills_missing"): result["skills_missing"] = ["No major gaps identified"]
        if not result.get("experience_match"): result["experience_match"] = "Fair"
        if not result.get("education_match"): result["education_match"] = "Fair"
        if not result.get("strengths"): result["strengths"] = ["Relevant background profile"]
        if not result.get("weaknesses"): result["weaknesses"] = ["No major concerns found"]
        if not result.get("interview_questions"): result["interview_questions"] = ["Tell me about your technical background?"]
        if not result.get("summary"): result["summary"] = f"{candidate_current_name} evaluation complete."
        
        return result

    print(f"🚀 Launching parallel parsing cluster for {len(resumes)} candidates...", flush=True)
    
    # ⚡ Execute up to 20 resume evaluations completely in parallel using workers
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Map tasks to the threads execution queue
        thread_results = list(executor.map(process_single_candidate, resumes))
        results.extend(thread_results)

    # Sort results sequentially by overall score parameter
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    print(f"✅ Parallel parsing batch complete! Returning ranked objects.", flush=True)
    return results
