from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from config import settings
import json
import time
import os
import concurrent.futures  # 👈 Added for high-volume parallel candidate processing

# Dynamic fallback setup for the Groq client
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
    """Score a single resume using Gemini Structured Output models with a strict Groq fallback"""

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

    # 1st Try: Primary generation using your working Gemini API configuration
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateEvaluation, # 👈 Enforces schema matching
                temperature=0.2
            )
        )
        return json.loads(response.text)

    except Exception as gemini_error:
        print(f"⚠️ Gemini processing unavailable or out of quota for {candidate_name}: {gemini_error}", flush=True)
        
        # 2nd Try: Seamlessly fall back to Groq Llama 3 API layer
        if groq_client:
            print(f"🚀 Routing {candidate_name} to Groq fallback layer...", flush=True)
            try:
                # Appending explicit keys matching CandidateEvaluation schema fields for Groq's text processor
                groq_instruction = (
                    f"{prompt}\n\n"
                    "CRITICAL: Return ONLY a raw JSON object string. Do not wrap it in markdown code block tags like ```json. "
                    "Do not include any greeting or text text conversational filler. Match these object dictionary keys exactly:\n"
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
                    response_format={"type": "json_object"}, # 👈 Enforces strict JSON string construction natively
                    temperature=0.1
                )
                
                raw_output = completion.choices[0].message.content.strip()
                return json.loads(raw_output)
                
            except Exception as groq_error:
                print(f"❌ Groq fallback engine also failed for {candidate_name}: {groq_error}", flush=True)
        else:
            print("⚠️ Groq client infrastructure skipped: GROQ_API_KEY missing from environment setup.", flush=True)

        # Fully populated fallback recovery data contract dictionary if both endpoints fail
        return {
            "candidate_name": candidate_name,
            "overall_score": 0,
            "match_percentage": 0,
            "skills_matched": ["Parsing failure fallback"],
            "skills_missing": ["Parsing failure fallback"],
            "experience_match": "Error",
            "education_match": "Error",
            "strengths": ["All active processing endpoints exhausted limits"],
            "weaknesses": [f"Gemini error context trace: {str(gemini_error)}"],
            "interview_questions": ["Could not process questions"],
            "recommendation": "Maybe",
            "summary": "Evaluation extraction ran into an unexpected token limit or active quota exhaustion block."
        }


def process_single_candidate(args) -> dict:
    """Helper worker to validate and manage field assignments for an isolated candidate profile"""
    jd_text, resume = args
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
    
    # Structural normalization assertions to match front-end template components safely
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


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score multiple resumes concurrently via thread pooling to support up to 20 profiles without timing out"""
    results = []
    
    print(f"🚀 Initializing parallel parsing cluster for {len(resumes)} candidates...", flush=True)
    
    # ⚡ Fires up to 5 workers simultaneously. Processing 20 resumes in quick batches prevents 
    # network socket drops while bypassing browser request timeouts entirely.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [(jd_text, resume) for resume in resumes]
        thread_futures = list(executor.map(process_single_candidate, tasks))
        results.extend(thread_futures)

    # Loop completes fully across all workers, then final arrays are sorted and ranked
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    print("✅ Parallel screening batch parsing completed successfully!", flush=True)
    return results
