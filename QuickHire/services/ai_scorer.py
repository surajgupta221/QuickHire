import concurrent.futures

def _validate_result(result: dict, candidate_name: str) -> dict:
    """Ensure all required keys exist and provide defaults if missing"""
    if not isinstance(result, dict):
        result = {}
        
    result["candidate_name"] = result.get("candidate_name", candidate_name)
    result["overall_score"] = result.get("overall_score", 0)
    result["match_percentage"] = result.get("match_percentage", 0)
    result["experience_match"] = result.get("experience_match", "Fair")
    result["education_match"] = result.get("education_match", "Fair")
    result["recommendation"] = result.get("recommendation", "Maybe")

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
        # Assumes _score_with_groq and _build_prompt exist elsewhere in your file
        result = _score_with_groq(prompt, candidate_name)
        return _validate_result(result, candidate_name)
    except Exception as groq_error:
        error_str = str(groq_error)
        print(f"❌ Groq failed for {candidate_name}: {error_str[:100]}", flush=True)

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
            # Assumes _score_with_gemini exists elsewhere in your file
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

    # Sort candidates by overall score to rank them cleanly
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
        
    # ✅ FIX: Removed the self-calling recursion loop that was crashing the app
    return results


def score_multiple_resumes(jd_text: str, resumes: list) -> list:
    """Parallel AI screening queue layer with concurrent processing"""
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

    # ✅ Apply the ranking tier sorting configurations safely before returning data
    results = apply_percentile_tiers(results)
    return results
