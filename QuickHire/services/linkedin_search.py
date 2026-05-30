import logging
import requests
import os
import re
from config import settings

logger = logging.getLogger(__name__)


def build_xray_query(job_title: str, location: str = "",
                     must_have_skills: str = "",
                     good_to_have_skills: str = "") -> str:
    """Build Google X-Ray search string for LinkedIn profiles"""

    # Base query
    query = f'site:linkedin.com/in "{job_title}"'

    # Add location
    if location:
        query += f' "{location}"'

    # Add must have skills
    if must_have_skills:
        skills = [s.strip() for s in must_have_skills.split(',') if s.strip()]
        for skill in skills[:3]:  # Use top 3 must-have skills
            query += f' "{skill}"'

    # Add good to have as OR
    if good_to_have_skills:
        skills = [s.strip() for s in good_to_have_skills.split(',') if s.strip()]
        if skills:
            or_skills = ' OR '.join([f'"{s}"' for s in skills[:2]])
            query += f' ({or_skills})'

    logger.info("Built X-Ray query: %s", query)
    return query


def search_linkedin_profiles(
    job_title: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    num_results: int = 10
) -> dict:
    """Search LinkedIn profiles using Google Custom Search API"""

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    logger.info(
        "Starting LinkedIn profile search: job_title=%s location=%s must_have=%s good_to_have=%s num_results=%s",
        job_title, location, must_have_skills, good_to_have_skills, num_results
    )

    if not api_key or not cx:
        logger.error("Google Search API not configured: GOOGLE_SEARCH_API_KEY or GOOGLE_SEARCH_ENGINE_ID missing")
        return {
            "error": "Google Search API not configured",
            "profiles": [],
            "query": ""
        }

    query = build_xray_query(
        job_title, location,
        must_have_skills, good_to_have_skills
    )

    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(num_results, 10),
                "gl": "in",  # India
                "lr": "lang_en"
            },
            timeout=10
        )

        data = response.json()

        if "error" in data:
            logger.error("Google CSE response error: %s", data["error"])
            return {
                "error": data["error"].get("message", "Search failed"),
                "profiles": [],
                "query": query
            }

        profiles = []
        items = data.get("items", [])
        logger.info("Google CSE returned %d items", len(items))

        for item in items:
            link = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Extract name from title (LinkedIn format: "Name - Title | LinkedIn")
            name = title.split(" - ")[0].strip() if " - " in title else title
            name = name.replace(" | LinkedIn", "").strip()

            # Extract job title from snippet
            job_info = ""
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) > 1:
                    job_info = parts[1].replace("| LinkedIn", "").strip()

            profiles.append({
                "name": name,
                "linkedin_url": link,
                "current_role": job_info,
                "snippet": snippet,
                "profile_id": link.split("/in/")[-1].strip("/") if "/in/" in link else ""
            })

        return {
            "query": query,
            "total_found": len(profiles),
            "profiles": profiles
        }

    except Exception as e:
        return {
            "error": str(e),
            "profiles": [],
            "query": query
        }