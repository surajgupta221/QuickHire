import time
from groq import Groq
from google.genai.errors import APIError

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
                response_schema=CandidateEvaluation, 
                temperature=0.2
            )
        )
        return json.loads(response.text)

    except APIError as google_err:
        if google_err.code == 429:
            print(f"⚠️ Gemini Quota hit (429) for {candidate_name}. Activating Groq fallback...", flush=True)
            
            if not groq_client:
                print("❌ Groq fallback failed: GROQ_API_KEY missing from environment setup.", flush=True)
                raise google_err
                
            # Groq Fallback Loop with Retry and Pacing Protection
            groq_retries = 3
            groq_delay = 6  # 6 seconds pacing window to clear free RPM walls
            
            for groq_attempt in range(groq_retries):
                try:
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
                        response_format={"type": "json_object"}, 
                        temperature=0.2
                    )
                    
                    return json.loads(groq_response.choices.message.content)
                    
                except Exception as groq_err:
                    # Catch Groq 429 rate limit errors or json validation flaws
                    print(f"⚠️ Groq engine attempt {groq_attempt + 1} failed: {groq_err}", flush=True)
                    if groq_attempt < groq_retries - 1:
                        print(f"Pacing Groq engine... Sleeping for {groq_delay}s", flush=True)
                        time.sleep(groq_delay)
                        groq_delay *= 2  # Exponential backoff pacing
                    else:
                        print(f"❌ All Groq fallback retries exhausted for {candidate_name}.", flush=True)
        else:
            print(f"⚠️ Gemini core API transmission error: {google_err}", flush=True)

    except Exception as e:
        print(f"⚠️ Gemini execution layer validation crash: {e}", flush=True)
        
    # Fully populated fallback recovery payload matching the schema definition if all processing engines fail
    return {
        "candidate_name": candidate_name,
        "overall_score": 0,
        "match_percentage": 0,
        "skills_matched": ["Parsing failure fallback"],
        "skills_missing": ["Parsing failure fallback"],
        "experience_match": "Error",
        "education_match": "Error",
        "strengths": ["All active processing endpoints exhausted limits"],
        "weaknesses": ["System hit API limit ceilings during execution"],
        "interview_questions": ["Could not process questions"],
        "recommendation": "Maybe",
        "summary": "Evaluation processing extraction ran into an unexpected system crash or quota exhaustion block."
    }
