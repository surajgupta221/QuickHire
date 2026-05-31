import asyncio
import aiohttp
import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import time


# ─── Configuration ────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_CX = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def build_xray_query(job_title: str, location: str = "",
                     must_have_skills: str = "",
                     source: str = "linkedin") -> str:
    """Build Google X-Ray search query for different sources"""

    skills = [s.strip() for s in must_have_skills.split(',') if s.strip()][:2]

    if source == "linkedin":
        query = f'site:linkedin.com/in "{job_title}"'
        if location and location.lower() not in ['all india', 'pan india']:
            query += f' "{location}"'
        for skill in skills:
            query += f' "{skill}"'

    elif source == "github":
        query = f'site:github.com "{job_title}"'
        for skill in skills:
            query += f' "{skill}"'

    elif source == "naukri":
        query = f'site:naukri.com "{job_title}"'
        if location:
            query += f' "{location}"'

    elif source == "indeed":
        query = f'site:indeed.com resume "{job_title}"'
        if location:
            query += f' "{location}"'

    elif source == "web":
        # Open web resume search
        query = f'resume "{job_title}" filetype:pdf OR filetype:doc'
        if location:
            query += f' "{location}"'
        for skill in skills:
            query += f' "{skill}"'

    else:
        query = f'"{job_title}" resume'
        if location:
            query += f' "{location}"'
        for skill in skills:
            query += f' "{skill}"'

    return query


def google_search(query: str, num: int = 10) -> List[Dict]:
    """Execute Google Custom Search and return results"""
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return []

    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX,
                "q": query,
                "num": min(num, 10),
            },
            timeout=10
        )
        data = response.json()

        if "error" in data:
            print(f"Google search error: {data['error'].get('message')}", flush=True)
            return []

        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "google"
            })
        return results

    except Exception as e:
        print(f"Google search failed: {e}", flush=True)
        return []


def search_linkedin_profiles(job_title: str, location: str = "",
                              must_have_skills: str = "",
                              num: int = 10) -> List[Dict]:
    """Search LinkedIn profiles via Google X-Ray"""
    query = build_xray_query(job_title, location, must_have_skills, "linkedin")
    raw_results = google_search(query, num)

    profiles = []
    for r in raw_results:
        link = r.get("link", "")
        if "linkedin.com/in/" not in link:
            continue

        title = r.get("title", "")
        # Parse: "Name - Title at Company | LinkedIn"
        name = title.split(" - ")[0].strip()
        name = name.replace(" | LinkedIn", "").strip()

        job_info = ""
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) > 1:
                job_info = parts[1].replace("| LinkedIn", "").strip()

        profile_id = link.split("/in/")[-1].strip("/").split("?")[0]

        profiles.append({
            "name": name,
            "profile_url": link,
            "current_role": job_info,
            "snippet": r.get("snippet", ""),
            "profile_id": profile_id,
            "source": "LinkedIn",
            "source_icon": "💼",
            "email": None,
            "can_find_email": bool(name and job_info)
        })

    return profiles


def search_github_profiles(job_title: str, must_have_skills: str = "",
                            num: int = 5) -> List[Dict]:
    """Search GitHub profiles for developers"""
    skills = [s.strip() for s in must_have_skills.split(',') if s.strip()]

    # Use GitHub API for developer search
    profiles = []

    if GITHUB_TOKEN and skills:
        for skill in skills[:2]:
            try:
                response = requests.get(
                    "https://api.github.com/search/users",
                    headers={
                        "Authorization": f"token {GITHUB_TOKEN}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    params={
                        "q": f"{skill} type:user",
                        "per_page": min(num, 10),
                        "sort": "followers"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    for user in data.get("items", [])[:num]:
                        # Get user details
                        try:
                            user_resp = requests.get(
                                f"https://api.github.com/users/{user['login']}",
                                headers={"Authorization": f"token {GITHUB_TOKEN}"},
                                timeout=5
                            )
                            if user_resp.status_code == 200:
                                u = user_resp.json()
                                profiles.append({
                                    "name": u.get("name") or u.get("login", "Unknown"),
                                    "profile_url": u.get("html_url", ""),
                                    "current_role": u.get("bio", ""),
                                    "snippet": f"📍 {u.get('location', 'N/A')} | ⭐ {u.get('public_repos', 0)} repos | 👥 {u.get('followers', 0)} followers",
                                    "profile_id": u.get("login", ""),
                                    "source": "GitHub",
                                    "source_icon": "🐙",
                                    "email": u.get("email"),
                                    "location": u.get("location", ""),
                                    "company": u.get("company", ""),
                                    "avatar": u.get("avatar_url", ""),
                                    "can_find_email": True
                                })
                        except Exception:
                            pass

            except Exception as e:
                print(f"GitHub search error: {e}", flush=True)

    # Also Google X-Ray GitHub
    query = build_xray_query(job_title, "", must_have_skills, "github")
    raw = google_search(query, 5)
    for r in raw:
        if "github.com/" in r.get("link", "") and "/in/" not in r.get("link", ""):
            name = r["title"].replace("GitHub - ", "").split(":")[0].strip()
            if name and name not in [p["name"] for p in profiles]:
                profiles.append({
                    "name": name,
                    "profile_url": r["link"],
                    "current_role": "",
                    "snippet": r.get("snippet", ""),
                    "source": "GitHub",
                    "source_icon": "🐙",
                    "email": None,
                    "can_find_email": False
                })

    return profiles[:num]


def search_open_web_resumes(job_title: str, location: str = "",
                             must_have_skills: str = "",
                             num: int = 5) -> List[Dict]:
    """Search open web for publicly available resumes"""
    query = build_xray_query(job_title, location, must_have_skills, "web")
    raw_results = google_search(query, num)

    resumes = []
    for r in raw_results:
        link = r.get("link", "")
        # Filter actual resume files/pages
        if any(ext in link.lower() for ext in ['.pdf', '.doc', '.docx', 'resume', 'cv', 'portfolio']):
            title = r.get("title", "Unknown")
            resumes.append({
                "name": title.split(" - ")[0].strip() if " - " in title else title,
                "profile_url": link,
                "current_role": "",
                "snippet": r.get("snippet", ""),
                "source": "Open Web",
                "source_icon": "🌐",
                "email": None,
                "can_find_email": False,
                "is_resume": True
            })

    return resumes


def find_email_hunter(name: str, domain: str = "") -> Optional[str]:
    """Find professional email using Hunter.io"""
    if not HUNTER_API_KEY or not name:
        return None

    try:
        # Split name
        parts = name.strip().split(" ")
        if len(parts) < 2:
            return None

        first_name = parts[0]
        last_name = parts[-1]

        if domain:
            # Find specific email at company
            response = requests.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": HUNTER_API_KEY
                },
                timeout=5
            )
            data = response.json()
            if data.get("data", {}).get("email"):
                return data["data"]["email"]
        else:
            # Email enrichment by name
            response = requests.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": HUNTER_API_KEY
                },
                timeout=5
            )
            data = response.json()
            if data.get("data", {}).get("email"):
                return data["data"]["email"]

    except Exception as e:
        print(f"Hunter.io error: {e}", flush=True)

    return None


def multi_source_search(
    job_title: str,
    location: str = "",
    must_have_skills: str = "",
    good_to_have_skills: str = "",
    num_results: int = 10,
    sources: List[str] = None,
    find_emails: bool = True
) -> Dict:
    """
    Multi-threaded search across all sources simultaneously
    Returns aggregated, deduplicated candidate list
    """

    if sources is None:
        sources = ["linkedin", "github", "web"]

    print(f"🔍 Multi-source search: {job_title} | {location} | sources: {sources}", flush=True)

    all_candidates = []
    per_source = max(num_results // len(sources), 3)

    # ─── Run searches in parallel ─────────────────────
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}

        if "linkedin" in sources:
            futures["linkedin"] = executor.submit(
                search_linkedin_profiles,
                job_title, location, must_have_skills, per_source
            )

        if "github" in sources:
            futures["github"] = executor.submit(
                search_github_profiles,
                job_title, must_have_skills, per_source
            )

        if "web" in sources:
            futures["web"] = executor.submit(
                search_open_web_resumes,
                job_title, location, must_have_skills, per_source
            )

        # Collect results
        for source, future in futures.items():
            try:
                results = future.result(timeout=15)
                all_candidates.extend(results)
                print(f"✅ {source}: found {len(results)} candidates", flush=True)
            except Exception as e:
                print(f"❌ {source} search failed: {e}", flush=True)

    # ─── Deduplicate ──────────────────────────────────
    seen_urls = set()
    unique_candidates = []
    for c in all_candidates:
        url = c.get("profile_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_candidates.append(c)

    # ─── Find emails in parallel ───────────────────────
    if find_emails and HUNTER_API_KEY:
        print("📧 Finding emails via Hunter.io...", flush=True)

        def enrich_email(candidate):
            if not candidate.get("email") and candidate.get("can_find_email"):
                email = find_email_hunter(candidate.get("name", ""))
                if email:
                    candidate["email"] = email
            return candidate

        with ThreadPoolExecutor(max_workers=3) as executor:
            enriched = list(executor.map(enrich_email, unique_candidates[:num_results]))
        unique_candidates[:num_results] = enriched

    # ─── Sort: email first, then by source quality ────
    unique_candidates.sort(key=lambda x: (
        0 if x.get("email") else 1,
        0 if x.get("source") == "GitHub" else 1,
        0 if x.get("source") == "LinkedIn" else 2,
    ))

    final = unique_candidates[:num_results]

    print(f"✅ Total candidates found: {len(final)}", flush=True)

    return {
        "total_found": len(final),
        "candidates": final,
        "sources_searched": sources,
        "emails_found": sum(1 for c in final if c.get("email")),
        "linkedin_count": sum(1 for c in final if c.get("source") == "LinkedIn"),
        "github_count": sum(1 for c in final if c.get("source") == "GitHub"),
        "web_count": sum(1 for c in final if c.get("source") == "Open Web")
    }