from google import genai
from google.genai import types
from google.genai.errors import APIError  # 👈 Added to cleanly detect Gemini 429 quota limits
from pydantic import BaseModel, Field
from typing import List
from config import settings
from groq import Groq  # 👈 Added Groq SDK
import json
import os
import time

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Initialize Groq Client (using API key from config settings or system environment variables)
# Make sure GROQ_API_KEY is added to your .env file or config setup
GROQ_API_KEY = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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
    """Score a single resume using Gemini Structured Output with an automatic Groq fallback engine"""

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

    # Increased contextual character window to 4000 characters for more accurate evaluation
    prompt = f"""
You are an expert technical recruiter evaluating {candidate_name} against this job requirement.
Analyze the experience, education, and technical alignment carefully.

JOB DESCRIPTION:
{jd_text[:4000]}

CANDIDATE RESUME:
{resume_text[:4000]}
"""

    try:
        # 1. Primary Attempt: Process using Gemini Natively
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

    except APIError as google_err:
        # 2. Intercept 429 Quota Exhausted limits specifically to activate fallback
        if google_err.code == 429:
            print(f"⚠️ Gemini Quota hit (429) for {candidate_name}. Activating Groq fallback...", flush=True)
            
            if not groq_client:
                print("❌ Groq fallback failed: GROQ_API_KEY missing from environment setup.", flush=True)
                raise google_err # Re-raise to trigger default dictionary payload initialization
                
            try:
                # Append explicit JSON formatting structural instructions for the fallback model
                groq_prompt = (
                    prompt + 
                    "\n\nReturn ONLY a valid JSON object matching this exact key structure:\n"
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
                
                groq_response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": groq_prompt}],
                    response_format={"type": "json_object"}, # 👈 Enforces explicit structural object constraints
                    temperature=0.2
                )
                
                return json.loads(groq_response.choices.message.content)
                
            except Exception as groq_err:
                print(f"❌ Fallback processing model also hit an unexpected crash: {groq_err}", flush=True)
        else:
            print(f"⚠️ Gemini core API transmission error: {google_err}", flush=True)

    except Exception as e:
        print(f"⚠️ Gemini output block failed: {e}", flush=True)
        
    # Fully populated fallback dictionary matching the exact schema definition if all engines fail
    return {
        "candidate_name": candidate_name,
        "overall_score": 0,
        "match_percentage": 0,
        "skills_matched": ["Parsing failure fallback"],
        "skills_missing": ["Parsing failure fallback"],
        "experience_match": "Error",
        "education_match": "Error",
        "strengths": ["Failed to extract structural arrays"],
        "weaknesses": ["Failed to extract structural arrays"],
        "interview_questions": ["Could not process questions"],
        "recommendation": "Maybe",
        "summary": "Evaluation processing extraction ran into an unexpected system crash or quota exhaustion block."
    }

def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Score multiple resumes and return ranked list of candidates"""
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
        
        # Safe normalization assertions
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

        # 🕒 Mandatory Rate-Limitation Safety Buffer
        # Free-tier allows 15 RPM (Requests Per Minute). Sleeping 4.5 seconds per resume prevents 
        # hitting the RPM wall during continuous candidate iterations.
        if i < len(resumes) - 1:
            print("Pacing API requests... Sleeping for 4.5 seconds", flush=True)
            time.sleep(4.5)

    # ✅ FIXED INDENTATION: Loop completes fully, then arrays are sorted and ranked
    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    for idx, item in enumerate(results):
        item["rank"] = idx + 1

    return results
